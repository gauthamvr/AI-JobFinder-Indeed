# AI Job finder using Indeed with ChatGPT Integration

An Indeed scraper that integrates with ChatGPT to find suitable jobs based on your profile and preferences, modifies your profile and skills section of your resume to include relevant keywords from the job description/profile, and completely automates the application process. Completely automates the application process for jobs with internal application button.
Tired of going through hundreds of jobs only to find that many are not suitable for you? You are at the right place. The code will analyze your profile and job descriptions to determine if you are a good fit for the role, and provides a curated list of jobs after going through the latest listing of jobs in Indeed. Automation of job application using AI in Indeed.

### Important Notes:
- **Please ensure to download the latest files to ensure that you have the latest page elements used by Indeed.**
- **Although I update the code with new elements, Indeed frequently changes its page elements. If you encounter logs indicating that elements could not be found, inspect the page and modify config.py with the correct elements.**
- **ChatGPT can make mistakes, so double-check important information.**
- **The code has been written to mimic user behavior, which may make it appear slow**
- **Make sure that the csv files and the previous chrome instance is closed before running**
- **If no api key is provided, it will only scrape the listings into the csv**
- **Run with chrome maximized (Recommended)**



## Applications

- Can be used as just a scraper
- Can be used just to identify suitable jobs based on your profile
- Can be used to apply automatically for the jobs that are suitable and have an internal application link.

## Features

- Scrapes the jobs from Indeed.
- Identifies suitable jobs based on user profiles.
- Automatically applies for suitable jobs.
- Automates the entire job application process for jobs that are suitable and have an internal application link.
- Automatically uploads the modified resume.
- Uses AI to answer employer questions based on your profile.
- Submits the job application.
- Loops through the next suitable job and applies automatically.


## How It Works:

1. The code opens Chrome, navigates to Indeed address provided in the `config.py`, and searches for the jobs you are looking for based on the keywords and pagination settings defined in `config.py`.
2. Sorts the jobs by date, with the newest at the top.
3. For each job detected, it uses ChatGPT to compare the job description/requirement with your profile and preferences (such as experience, education, etc.) as outlined in `config.py`, and determines if you're suitable for the job.
4. If the job is deemed suitable, the **profile** and **skills** sections in the resume template `template.docx` are modified to include relevant keywords, ensuring your resume passes through Applicant Tracking Systems (ATS).
5. You can modify or replace `template.docx` with your own resume, but ensure that the placeholders for **profile** and **skills** match those defined in `config.py`.
6. The modified resume is saved in the `resume` folder, named with the job title and job ID for later use.
7. Processed job details are stored in two CSV files:
   - `latest_jobs.csv`: Contains details from the most recent job search.
   - `master_jobs.csv`: Tracks all jobs processed to date, preventing duplication and minimizing load on Indeed.
8. The CSV files contain comprehensive job information, including job title, job ID, date, resume location, suitability, apply link, and more.
9. Once pagination limits are reached, the script moves on to searching for the next job using the keyword from `config.py` and repeats the process.
10. You can manually review suitable jobs identified by ChatGPT and apply using the resumes in the `resume` folder  or you can enable auto_apply to apply for jobs automatically using the modified resume.
11. If you want to auto-apply for jobs that has an internal application button:
       - Ensure you are logged in to Indeed in the browser used by the program.
       - Make sure the 'auto_apply' is set to "Yes" and 'final_apply_button' is set to "Yes" in the `config.py` file.
       - The program will automatically answer questions asked by the employer based on your profile.
       - Therefore, it is essential to ensure that 'profile_answer_questions' in the `config.py` file contains all the necessary information.
       - Add or modify the two profiles in the `config.py` to suit your needs/based on the common questions you face from the employer.
       - If the answer is not available in the 'profile_answer_questions', ChatGPT might generate an inaccurate response, so please be cautious.
       - If 'final_apply_button' is not set to "Yes", the program will not click the final submit button at the end of the application.
       - Feel free to test everything to ensure it works properly before enabling the final submit button.
12. Answers/responses generated by ChatGPT can be found in a CSV file or as an HTML file in the 'Submissions' folder.

## Installation 🔌

[![Watch the video](https://img.youtube.com/vi/nLqj_ijwzCA/0.jpg)](https://youtu.be/nLqj_ijwzCA)

### Prerequisites:
- Ensure **Python** and **pip** are installed on your machine.
- Ensure **Google Chrome** is installed.
- **Openai api key**

### Steps:
1. Download the zip file or
   Clone the repository if you have git installed:
   ```bash
   git clone https://github.com/gauthamvr/AI-JobFinder-Indeed.git


3. Navigate to the project folder and open a terminal/cmd (or use your preferred IDE).

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
5. Enter your **OpenAI API key** and profile details in `config.py`.

6. Modify `config.py` according to your requirements (keywords, pagination, etc.).

7. Run the main script:
   ```bash
   python main.py

8. Job details will be saved in two CSV files.
  
   - `latest_jobs.csv`: Contains details from the most recent job search.
   - `master_jobs.csv`: Tracks all jobs processed to date, preventing duplication and minimizing load on Indeed.

9. If you want to auto-apply for jobs that has an internal application button:
    - Ensure you are logged in to Indeed in the browser used by the program.
    - Make sure the 'auto_apply' is set to "Yes" and 'final_apply_button' is set to "Yes" in the config.py file.

Generated resumes can be found in the `resume` folder, named with the job title and job ID for easy identification. Gnerated sumbissions can be found in the 'Submissions' folder.

You can manually review the CSV files to identify suitable jobs and apply using the generated resumes or you can chose to autoapply (detailed at the top).
If you see "Error" in all rows of the suitability column in the CSV, check if you have correctly saved the OpenAI key in `config.py`. Then, delete the CSV files and try running `main.py` again.

**Note:** Deleting the CSV will result in all jobs being processed again, so it is not recommended unless necessary.








## Detailed Installation Guide:

1. Install the **Google Chrome** browser.
2. Install **Python** (download from [here](https://www.python.org/downloads/)).
3. Download the zip file by pressing the green button or
   Clone the repository if you have git installed using the terminal/cmd:
   ```bash
   git clone https://github.com/gauthamvr/AI-JobFinder-Indeed.git


5. Navigate to the project folder in the terminal, or open a terminal/IDE in the downloaded project folder. If you downloaded the zip, extract it and navigate to the extracted folder.
6. Install the required dependencies by running the command in terminal/IDE:
   ```bash
   pip install -r requirements.txt

7. Open the `config.py` file and Enter your OpenAI API key and profile details.
8. Modify config.py as needed.
9. Run the script:
   ```bash
   python main.py

10. Job details will be saved in two CSV files. Generated resumes will be stored in the resume folder. Submissions will be in the Submissions folder



## Recommendations:

- Monitor the first few runs to handle pop-ups, verifications, etc.
- **Be responsible** to avoid overloading Indeed's site.
- If a verification page appears, the program might fail, so it's recommended to use a Chrome profile. Captchas will require manual intervention.



## Future Plans:

- Expand testing and ensure compatibility with all Indeed domains.


Feel free to contact me for any updates, requests, questions, or donations. Any contributions are greatly appreciated.


## Buy me a coffee:
Your support is greatly appreciated! Every contribution helps.

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-donate-yellow)](https://buymeacoffee.com/gauthamvr)



    
