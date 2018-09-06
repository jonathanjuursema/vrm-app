# Application for Visual Role Mining
This repository contains the code for a proof-of-concept visual role mining application. This application has been built as part of my [master thesis](https://essay.utwente.nl/76341/). This thesis also contains more information regarding this application.

# Installation
This application is built for `Python 3`. Dependencies are laid out in `requirements.txt`. If you want to make changes to the JavaScript, you should change the `js/matrix_visualisation.ts` TypeScript file and use TypeScript to compile a JavaScript file and place it under `static/js/matrix_visualisation.js`. You run the application by running `server.py`. This opens a webserver on `localhost:8080`. There is no authentication and no support for HTTPS, so make sure not to leave your data open to the internet.

# Data
Input files can be uploaded via the web interface. All input files use the `.csv` format. Please see the `input-examples` directory for examples of the file structure.

# Disclaimer
This application is a proof of concept and is only intended to be a means for validating the implemented concepts. It is explicitly not intended to be used as a commercial product, and should also not be used as the basis for a commercial product. It is not written to be modular, easy to change or easy to improve upon. It was written to get the job done.

Having said that, if you have any questions, feel free to open an issue!
