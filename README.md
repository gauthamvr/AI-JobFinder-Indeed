# Indeed Scraper with ChatGPT Integration

An Indeed scraper that integrates ChatGPT to find suitable jobs based on your profile, modify your resume to include relevant keywords from the job description, and automate parts of the application process.

### Important Notes:
- **Please use responsibly.**
- **ChatGPT can make mistakes, so double-check important information.**
- **Currently tested only on [Indeed UK](https://uk.indeed.com/) using Chrome browser.**
- **This is the free version.**

## How It Works:

1. The script opens Chrome, navigates to Indeed UK, and searches for jobs based on the keywords and pagination settings defined in `config.py`.
2. Sorts the jobs by date, with the newest at the top.
3. For each job detected, it uses ChatGPT to compare the job details with your profile (such as experience, education, etc.) as outlined in `config.py`, and determines if you're suitable for the job.
4. If the job is deemed suitable, the **profile** and **skills** sections in `template.docx` are modified to include relevant keywords, ensuring your resume passes through Applicant Tracking Systems (ATS).
5. You can modify or replace `template.docx` with your own resume, but ensure that the placeholders for **profile** and **skills** match those defined in `config.py`.
6. The modified resume is saved in the `resume` folder, named with the job title and job ID for later use.
7. Processed job details are stored in two CSV files:
   - `latest_jobs.csv`: Contains details from the most recent job search.
   - `master_jobs.csv`: Tracks all jobs processed to date, preventing duplication and minimizing load on Indeed.
8. The CSV files contain comprehensive job information, including job title, job ID, date, resume location, suitability, apply link, and more.
9. Once pagination limits are reached, the script moves on to the next keyword from `config.py` and repeats the process.
10. You can manually review suitable jobs identified by ChatGPT and apply using the resumes in the `resume` folder.

## Installation 🔌

### Prerequisites:
- Ensure **Python** and **pip** are installed on your machine.
- Ensure **Google Chrome** is installed.
- Openai api key

### Steps:
1. Clone the repository:
   ```bash
   git clone https://github.com/gauthamvr/Indeed-scraper-automation-AI.git
or download the zip file.

2. Navigate to the project folder and open a terminal (or use your preferred IDE).

3. Install the required dependencies:
   ```bash
   pip3 install -r requirements.txt
4. Enter your **OpenAI API key** and profile details in `config.py`.

5. Modify `config.py` according to your requirements (keywords, pagination, etc.).

6. Run the main script:
   ```bash
   python main.py

8. Job details will be saved in two CSV files.
  
   - `latest_jobs.csv`: Contains details from the most recent job search.
   - `master_jobs.csv`: Tracks all jobs processed to date, preventing duplication and minimizing load on Indeed.

Generated resumes can be found in the `resume` folder, named with the job title and job ID for easy identification.

You can manually review the CSV files to identify suitable jobs and apply using the generated resumes.
If you see "Error" in all rows of the suitability column in the CSV, check if you have correctly saved the OpenAI key in `config.py`. Then, delete the CSV files and try running `main.py` again.

**Note:** Deleting the CSV will result in all jobs being processed again, so it is not recommended unless necessary.


## Pro Version (Features)

- Automates the entire job application process for jobs that are suitable and have an internal application link.
- Automatically uploads the modified resume.
- Uses AI to answer employer questions based on your profile.
- Submits the job application.
- Loops through the next suitable job and applies automatically.

**Note:** Currently, the pro version is only available by contacting me or through a donation.




## Detailed Installation Guide:

1. Install the **Google Chrome** browser.
2. Install **Python** (download from [here](https://www.python.org/downloads/)).
4. Clone the repository:
   ```bash
   git clone https://github.com/gauthamvr/Indeed-scraper-automation-AI.git
or download the zip file.

5. Navigate to the project folder in the terminal, or open a terminal/IDE in the downloaded project folder.
6. Install Selenium
   ```bash
   pip install selenium
7. Install requests
   ```bash
   pip install requests
8. Install python-docx
   ```bash
   pip install python-docx
9. Enter your OpenAI API key and profile details in the config.py file.
10. Modify config.py as needed.
1. Run the script:
   ```bash
   python main.py
12. Job details will be saved in two CSV files. Generated resumes will be stored in the resume folder.



## Recommendations:

- Monitor the first few runs to handle pop-ups, verifications, etc.
- **Be responsible** to avoid overloading Indeed's site.
- If a verification page appears, the program might fail, so it's recommended to use a Chrome profile. Captchas will require manual intervention.

#### Chrome Profile Setup (Recommended):

1. Create a new profile on Chrome.
2. Launch the new profile, go to [Indeed UK](https://uk.indeed.com/), and log in (optional but recommended).
3. Copy the root folder location of your Chrome profile.
4. Paste the profile path into the commented section of `main.py` and uncomment the relevant code to use the profile.

Feel free to contact me for any updates, requests, questions, or donations. Any contributions are greatly appreciated.

If anyone from Indeed—or anyone for that matter—sees this, please consider recruiting me, I'm looking for a job.


    
