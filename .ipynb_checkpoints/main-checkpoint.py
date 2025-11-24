import os
import pandas as pd
import numpy as np

import gradio as gr

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity



from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "admitguide_requests_total",
    "Total number of requests received",
    ["endpoint"]
)

RESPONSE_TIME = Histogram(
    "admitguide_response_seconds",
    "Response time for each request",
    ["endpoint"]
)

FEEDBACK_COUNT = Counter(
    "admitguide_feedback_total",
    "Total number of feedback submissions"
)


DATA_PATH = os.path.join(os.path.dirname(__file__), "university_admission_requirements.xlsx")

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"Dataset not found at {DATA_PATH}. "
        f"Place 'university_admission_requirements.xlsx' in the project folder."
    )

df = pd.read_excel(DATA_PATH)

required_columns = [
    "University",
    "Location (State)",
    "Program Strength Area",
    "Average GRE Required",
    "Average TOEFL Required",
    "Average IELTS Required",
    "Minimum CGPA Required",
    "Acceptance Rate (%)",
    "University Rating (1-5)",
]

missing = [c for c in required_columns if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns in dataset: {missing}")

df["Admission_Label"] = (
    (df["Minimum CGPA Required"] <= 3.4).astype(int)
    + (df["Average GRE Required"] <= 320).astype(int)
    + (df["Average TOEFL Required"] <= 100).astype(int)
    + (df["University Rating (1-5)"] <= 3).astype(int)
)
df["Admission_Label"] = (df["Admission_Label"] >= 2).astype(int)



num_features = [
    "Average GRE Required",
    "Average TOEFL Required",
    "Average IELTS Required",
    "Minimum CGPA Required",
    "Acceptance Rate (%)",
    "University Rating (1-5)",
]

cat_features = ["University", "Location (State)", "Program Strength Area"]

preprocessor = ColumnTransformer(
    transformers=[
        ("num", MinMaxScaler(), num_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
    ]
)

rf_model = RandomForestClassifier(
    n_estimators=200,
    criterion="gini",
    random_state=42,
)

pipeline = Pipeline(
    steps=[
        ("preprocess", preprocessor),
        ("model", rf_model),
    ]
)

X = df[num_features + cat_features]
y = df["Admission_Label"]
pipeline.fit(X, y)



df["Program_Description"] = (
    df["University"].astype(str)
    + " | Program Area: " + df["Program Strength Area"].astype(str)
    + " | Location: " + df["Location (State)"].astype(str)
)

tfidf_vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = tfidf_vectorizer.fit_transform(df["Program_Description"].fillna(""))

def find_university_row(university_name: str):
    if not isinstance(university_name, str) or not university_name.strip():
        return None
    mask = df["University"].str.lower() == university_name.strip().lower()
    if mask.any():
        return df[mask].iloc[0]
    return None



@RESPONSE_TIME.labels("admission_predict").time()
def predict_admission_student(gre, toefl, ielts, cgpa, university, feedback):
    REQUEST_COUNT.labels("admission_predict").inc()
    try:
        uni_row = find_university_row(university)
        if uni_row is None:
            return (
                "<b>University not found in dataset.</b><br>"
                "Enter the exact university name as in the dataset."
            )

        req_gre = float(uni_row["Average GRE Required"])
        req_toefl = float(uni_row["Average TOEFL Required"])
        req_ielts = float(uni_row["Average IELTS Required"])
        req_cgpa = float(uni_row["Minimum CGPA Required"])

        match_score = (
            int(gre >= req_gre)
            + int(toefl >= req_toefl)
            + int(ielts >= req_ielts)
            + int(cgpa >= req_cgpa)
        )

        uni_features = pd.DataFrame(
            [{
                "Average GRE Required": req_gre,
                "Average TOEFL Required": req_toefl,
                "Average IELTS Required": req_ielts,
                "Minimum CGPA Required": req_cgpa,
                "Acceptance Rate (%)": float(uni_row["Acceptance Rate (%)"]),
                "University Rating (1-5)": float(uni_row["University Rating (1-5)"]),
                "University": str(uni_row["University"]),
                "Location (State)": str(uni_row["Location (State)"]),
                "Program Strength Area": str(uni_row["Program Strength Area"]),
            }]
        )

        difficulty_prob = pipeline.predict_proba(uni_features)[0][1]
        final_prob = ((match_score / 4) * 0.7 + difficulty_prob * 0.3) * 100
        final_prob = round(final_prob, 2)

        if isinstance(feedback, str) and feedback.strip():
            with open(os.path.join(os.path.dirname(__file__), "feedback_log.txt"), "a", encoding="utf-8") as f:
                f.write(feedback.strip() + "\n")
            FEEDBACK_COUNT.inc()

        html = f"""
        <h3>Admission Evaluation for {uni_row['University']}</h3>
        <b>Final Admission Probability:</b> {final_prob}%<br>
        <b>Requirement Match Score:</b> {match_score} / 4<br>
        <b>University Difficulty Score:</b> {round(difficulty_prob*100, 2)}%<br><br>
        """
        return html
    except Exception as e:
        return f"<b>Error during prediction:</b> {e}"



@RESPONSE_TIME.labels("program_search").time()
def search_programs(interest_text):
    REQUEST_COUNT.labels("program_search").inc()
    try:
        if not interest_text or not interest_text.strip():
            return "Please enter at least one keyword describing your interests."

        query_vec = tfidf_vectorizer.transform([interest_text.strip()])
        sims = cosine_similarity(query_vec, tfidf_matrix)[0]

        results = df.copy()
        results["Similarity"] = sims
        results = results[results["Similarity"] > 0.05]

        if results.empty:
            return "No universities matched your interest."

        results = results.sort_values(by="Similarity", ascending=False)

        display_cols = [
            "University",
            "Location (State)",
            "Program Strength Area",
            "Average GRE Required",
            "Minimum CGPA Required",
            "Acceptance Rate (%)",
            "University Rating (1-5)"
        ]

        return results[display_cols].to_html(index=False)

    except Exception as e:
        return f"Error during search: {e}"



def build_app():
    with gr.Blocks(title="Admit-Guide") as demo:
        gr.Markdown("""
        This system provides:
        - Admission prediction based on your academic profile  
        - Program & University search based on your interests  
        """)

        with gr.Tab("Admission Predictor"):
            gre = gr.Number(label="Your GRE Score", value=320)
            toefl = gr.Number(label="Your TOEFL Score", value=100)
            ielts = gr.Number(label="Your IELTS Score", value=7)
            cgpa = gr.Number(label="Your CGPA", value=3.5)
            uni = gr.Textbox(label="University Name")
            feedback = gr.Textbox(label="Feedback (optional)")

            out = gr.HTML()
            gr.Button("Predict").click(
                predict_admission_student,
                [gre, toefl, ielts, cgpa, uni, feedback],
                out
            )

        with gr.Tab("Program Finder"):
            interest = gr.Textbox(label="Describe your interests")
            out2 = gr.HTML()
            gr.Button("Search").click(
                search_programs,
                [interest],
                out2
            )

    return demo



from prometheus_client import start_http_server

start_http_server(8000)




if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860)
