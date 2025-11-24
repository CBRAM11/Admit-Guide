Admit-Guide:
1. Project Overview

Admit-Guide is an intelligent university admission assistant designed to help students evaluate their admission chances and discover suitable programs based on their academic interests.
The system offers:

Admission Probability Prediction using a Random Forest model

Program & University Search via TF-IDF semantic matching

Two-tab Gradio Interface

Trustworthiness Components

Monitoring Stack with Prometheus and Grafana

Full Deployment with Docker Compose

This system demonstrates end-to-end AI system development aligned with HCI, trustworthiness, monitoring, and deployment best practices.


2) Structure:

📁 Admit-Guide
│
├── 📁 src
│   ├── main.py
│   ├── requirements.txt
│   ├── university_admission.xlsx
│   ├── models/
│   ├── utils/
│   ├── data/
│
├── 📁 deployment
│   ├── Dockerfile
│   ├── docker-compose.yml
│
├── 📁 monitoring
│   ├── 📁 prometheus
│   │   ├── prometheus.yml
│   ├── 📁 grafana
│       ├── dashboards.json
│
├── 📁 documentation
│   ├── README.md
│   ├── AI System project proposal template
│   ├── Project report.docx
│
├── 📁 videos
│   ├── system_demo.mp4
│
└── .gitignore

3) System entry point:

Run the following command to execute and run the porject


cd src
pip install -r requirements.txt
python main.py


4) Docker implementation:

docker compose down
docker compose up --build


6) Video Demonstration:

A complete walkthrough of:

The Gradio UI

Admission prediction

Program search

Dockerized deployment

Prometheus scraping

Grafana dashboards

videos/system_demo.mp4-folder where the video is available


7) Deployment Strategy

The system uses Docker Compose for multi-service deployment:

Services

Admit-Guide Application

Python + Gradio frontend

ML inference

Metrics exposed at /metrics

Prometheus

Scrapes system/application metrics

Uses monitoring/prometheus/prometheus.yml

Grafana Visual dashboard for:

Request count

Response latency

Feedback events

System performance

8. Monitoring and Metrics
Tools Used

Prometheus: Scrapes and stores system metrics

Grafana: Dashboards for visualization

Application-Level Metrics

Request Count

admitguide_requests_total


Response Time Histogram

admitguide_response_seconds


Feedback Count

admitguide_feedback_total

System Metrics
(CPU, memory, container health via Prometheus)


9) Document:
AI System Project Proposal-/documentation/AI System project proposal template
Final Project Report-/documentation/Project report.docx
Developer README-/documentation/README.md


10) Version Control and Team Collaboration:

The project uses Git for source control with:

Frequent atomic commits

Branching for major features

Version tagging during deployment stages

Clear commit messages documenting model changes, UI changes, and monitoring updates