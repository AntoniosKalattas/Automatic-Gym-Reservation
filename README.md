# Automatic-Gym-Reservation


Automatic-Gym-Reservation is an automation tool for reserving gym sessions at my Uni. It uses Python and Selenium WebDriver to interact with the UCY gym reservation system, automating the entire booking process.

## Features

- **Automated Reservations**: Book gym sessions quickly without manual interaction.
- **Cross-Platform Compatibility**: Works on Windows, macOS, and Linux systems with Python and Selenium.
- **User-Friendly Setup**: Easily configurable through the provided scripts.

## Prerequisites

- [Python 3.x](https://www.python.org/downloads/)
- [Google Chrome Browser](https://www.google.com/chrome/)
- [ChromeDriver](https://sites.google.com/chromium.org/driver/) (compatible with your Chrome version)
- [Electron](https://www.electronjs.org/) for additional GUI-based features

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/AntoniosKalattas/UCYGYM_BOT.git
   cd UCYGYM_BOT
   ```

2. **Install Dependencies**:

   Use the `requirements.txt` file for Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Setup

### Set Up ChromeDriver

- Download [ChromeDriver](https://googlechromelabs.github.io/chrome-for-testing/) for your OS.
- Place it in your system's PATH or specify its location in the script.

### Copy the path to chrome profile

- enter `chrome://version` in chrome url
- copy the location of `profile path` inside the `chromeProfilePath.txt` file

### Email Setup (optional)

1.  **Enable 2-Step Verification:** If you haven't already, you'll need to enable 2-Step Verification on your Google account. You can do that here: [https://myaccount.google.com/security](https://myaccount.google.com/security)

2.  **Generate an App Password:**
    *   Go to this page: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
    *   When prompted, select "Other (Custom name)" for the app and give it a name like "Gym Reservation".
    *   Click "Generate".

3.  **Use the App Password:**
    *   Google will give you a 16-digit password. Copy this password.
    *   Create a `.env` file in the root of the project.
    *   Add the following lines to the `.env` file, replacing `<your_email>` and `<your_app_password>` with your actual email and the 16-digit App Password you just generated:
        ```
        EMAIL_USER="<your_email>"
        EMAIL_PASSWORD="<your_app_password>"
        ```

## Usage

1.  **Run the self-test script** to ensure that everything is set up correctly:
    ```bash
    python selfTest.py
    ```
2.  **Run the main script** to start the automatic reservation process:
    ```bash
    python auto.py
    ```

    
# How to setup automatic reservation
   - Choose the desired time of the reservation in `auto.py`
   - In your LINUX server run the command
```bash
nohup python3 auto.py &
```

## Files and Structure

- **`autoReservation.py`**: Main script for automating reservations.
- **`firstTime.py`**: Script for initial configuration.
- **`package.json`**: Configuration file for Electron integration.
- **`requirements.txt`**: Python dependencies for Selenium and other packages.

## Troubleshooting

- **Selenium Errors**: Ensure that ChromeDriver matches your Chrome browser version.
- **Element Not Found**: Verify that the UCY reservation system hasn't changed its structure. Update the selectors in the scripts if necessary.
- **Node.js Issues**: Ensure Node.js is installed to run Electron.

# UI Version (not Supported)

   Ensure Electron dependencies are installed via npm(Only for UI perposes):

   ```bash
   npm install
   ```

### Start with Electron (Optional)

For a GUI-based experience, launch the Electron app:

```bash
npm start
```


## Contributing

Contributions are welcome! Feel free to fork the repository, submit a pull request, or open an issue.

## License

This project is licensed under the ISC License. See the `LICENSE` file for details.

## Author

Created by [Antonios Kalattas](https://github.com/AntoniosKalattas).

---
![My Project Logo](https://github.com/AntoniosKalattas/UCYGYM_BOT/blob/main/img/mainScreen.png)


## Troubleshooting

- **Selenium Errors**: Ensure that ChromeDriver matches your Chrome browser version.
- **Element Not Found**: Verify that the UCY reservation system hasn't changed its structure. Update the selectors in the scripts if necessary.
- **Node.js Issues**: Ensure Node.js is installed to run Electron.

# UI Version (not Supported)

   Ensure Electron dependencies are installed via npm(Only for UI perposes):

   ```bash
   npm install
   ```

### Start with Electron (Optional)

For a GUI-based experience, launch the Electron app:

```bash
npm start
```


## Contributing

Contributions are welcome! Feel free to fork the repository, submit a pull request, or open an issue.

## License

This project is licensed under the ISC License. See the `LICENSE` file for details.

## Author

Created by [Antonios Kalattas](https://github.com/AntoniosKalattas).

---
![My Project Logo](https://github.com/AntoniosKalattas/UCYGYM_BOT/blob/main/img/mainScreen.png)
