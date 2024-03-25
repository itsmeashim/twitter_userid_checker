# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /usr/src/app

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Download and install ChromeDriver
RUN wget -N https://storage.googleapis.com/chrome-for-testing-public/123.0.6312.58/linux64/chrome-linux64.zip -P /tmp \
    && unzip /tmp/chrome-linux64.zip -d /usr/local/bin \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chrome-linux64.zip

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run main.py when the container launches
CMD ["python", "./main.py"]
