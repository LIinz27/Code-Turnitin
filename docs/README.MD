# Code Turnitin: Plagiarism Checker for Programming Assignments

## Overview

This project implements a web-based code plagiarism detection system, inspired by Turnitin, specifically designed for programming assignments. It helps educators identify similarities between student code submissions and also against public code repositories like GitHub, utilizing Jaccard Similarity for token-based code comparison.

The system is built with a Python Flask backend for core logic (code scraping, preprocessing, and similarity checking) and a straightforward HTML, CSS, and JavaScript frontend for user interaction.

## Features

* **Student Code Upload:** Allows users to upload multiple student code files for analysis.
* **GitHub URL Integration:** Supports adding specific GitHub `blob` URLs to compare student code against public repositories.
* **Similarity Detection (Mahasiswa vs GitHub):** Compares uploaded student code against the scraped GitHub code.
* **Similarity Detection (Mahasiswa vs Mahasiswa):** Detects similarities among submitted student codes to identify potential collusion.
* **Pre-processing:** Basic code pre-processing to remove comments (Python, JavaScript) and normalize whitespace to enhance comparison accuracy.
* **Jaccard Similarity:** Employs the Jaccard index to quantify the similarity between code token sets.
* **Web Interface:** User-friendly web interface for easy file uploads, URL input, and result viewing.
* **Clear & Sorted Results:** Displays similarity scores in a structured table, sorted by relevance, with visual highlights for high similarity.

## Technologies Used

* **Backend:** Python (Flask, Requests, BeautifulSoup4)
* **Frontend:** HTML, CSS, JavaScript
* **Similarity Algorithm:** Jaccard Similarity

## Project Structure

CODE TURNITIN/
├── .venv/                     # Python Virtual Environment
├── data/
│   ├── github/                # Stores scraped raw code from GitHub
│   └── mahasiswa/             # Stores uploaded student code files
├── app.py                     # Flask backend application
├── app.js                     # Frontend JavaScript logic
├── github_scraper.py          # Script for scraping raw code from GitHub URLs
├── similarity_checker.py      # Core logic for code preprocessing and Jaccard similarity calculation
├── index.html                 # Main frontend HTML file
└── style.css                  # Frontend CSS for styling

## Setup and Installation

Follow these steps to get the project up and running on your local machine:

1. **Clone the Repository (if applicable):**

   ```bash
   git clone <your-repository-url>
   cd Code Turnitin
   ```

   (If this is not a Git repo yet, just navigate to your project directory.)
2. **Create a Python Virtual Environment:**
   It's recommended to use a virtual environment to manage project dependencies.

   ```bash
   python -m venv .venv
   ```
3. **Activate the Virtual Environment:**

   * **Windows:**
     ```bash
     .\.venv\Scripts\activate
     ```
   * **macOS / Linux:**
     ```bash
     source ./.venv/bin/activate
     ```
4. **Install Dependencies:**
   Install all required Python packages using the `requirements.txt` file.

   ```bash
   pip install -r requirements.txt
   ```
5. **Prepare Data Directories:**
   The `data/mahasiswa` and `data/github` directories will be created automatically by `app.py` if they don't exist, but you can create them manually for clarity.

   ```bash
   mkdir -p data/mahasiswa
   mkdir -p data/github
   ```

## How to Run

1. **Activate your virtual environment** (if not already active, see step 3 in Setup).
2. **Run the Flask Application:**

   ```bash
   python app.py
   ```

   You should see output indicating that the Flask development server is running, typically on `http://127.0.0.1:5000/`.
3. **Access the Web Interface:**
   Open your web browser and navigate to `http://127.0.0.1:5000/`.

## Usage

1. **Upload Student Code:**

   * Click "Pilih File Kode Mahasiswa" (Select Student Code Files).
   * Select one or more `.js`, `.py`, `.java`, or other code files from your local machine. The selected files will appear in the list. You can remove them by clicking 'X'.
2. **Add GitHub URLs:**

   * In the "Tambahkan URL GitHub" section, paste a GitHub `blob` URL (e.g., `https://github.com/user/repo/blob/branch/file.js`) into the input field.
   * Click "Tambah URL" (Add URL). The URL will be added to the list below.
3. **Run Analysis:**

   * Once you have uploaded student files and optionally added GitHub URLs, click the "Jalankan Deteksi Kemiripan" (Run Similarity Detection) button.
   * A "Analisis sedang berjalan..." (Analysis in progress...) indicator will appear.
4. **View Results:**

   * After the analysis is complete, the "Hasil Deteksi Kemiripan" (Similarity Detection Results) section will appear.
   * Results will be displayed in two tables: "Mahasiswa vs GitHub" and "Mahasiswa vs Mahasiswa", showing the similarity percentage.
   * Rows with a similarity score of 70% or higher will be highlighted.

## Contributing

Feel free to fork the repository, open issues, and submit pull requests.

---

**Developed by:** [Your Name/Team Name]
**Contact:** [Your Email/Link to Profile]
**Date:** 3 Juni 2025
