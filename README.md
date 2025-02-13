# Automatic-Gym-Reservation


Automatic-Gym-Reservation is an automation tool for reserving gym sessions at the University of Cyprus. It uses Python and Selenium WebDriver to interact with the UCY gym reservation system, automating the entire booking process.

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

   Ensure Electron dependencies are installed via npm(Only for UI perposes):

   ```bash
   npm install
   ```

3. **Set Up ChromeDriver**:

   - Download [ChromeDriver](https://googlechromelabs.github.io/chrome-for-testing/) for your OS.
   - Place it in your system's PATH or specify its location in the script.
   
4. **Copy the path to chrome profile**:
   
   - enter `chrome://version` in chrome url
   - copy the location of `profile path` inside the `chromeProfilePath.txt` file

## Usage

### Start with Electron (Optional)

For a GUI-based experience, launch the Electron app:

```bash
npm start
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

# How to setup automatic reservation
   - Choose the desired time of the reservation in `auto.py`
   - In your LINUX server run the command
```bash
nohup python3 auto.py &
```
     


## Contributing

Contributions are welcome! Feel free to fork the repository, submit a pull request, or open an issue.

## License

This project is licensed under the ISC License. See the `LICENSE` file for details.

## Author

Created by [Antonios Kalattas](https://github.com/AntoniosKalattas).

---
![My Project Logo](https://github.com/AntoniosKalattas/UCYGYM_BOT/blob/main/img/mainScreen.png)
