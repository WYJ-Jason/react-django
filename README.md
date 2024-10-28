# Next-React Django Project

This project is a full-stack application using Next.js and Django.


## Prerequisites

Before you begin, ensure your development environment meets the following prerequisites:

- **Python**: 3.10.6
- **Node.js**: 20.10.0
- **npm**: 10.2.5

## Installation Guide

1. **Install Python**  
   Visit the [official Python website](https://www.python.org/downloads/) to download and install the appropriate version for your operating system.

2. **Install Node.js**  
   Visit the [official Node.js website](https://nodejs.org/) to download and install the appropriate version for your operating system.

3. **Install npm**  
   npm is typically installed with Node.js. If you need to update npm, run the following command:
   ```bash
   npm install -g npm

## Getting Started

### 1. Clone the Project

```bash
git clone https://github.com/WYJ-Jason/react-django.git
cd react-django
```

### 2. Set Up the Backend (Django)
#### 2.1 Create a Virtual Environment

Create a virtual environment in the backend folder:

```bash
cd backend
python -m venv venv
```

#### 2.2 Activate the Virtual Environment
##### Windows:
``` bash
venv\Scripts\activate
```
##### macOS/Linux:
```bash
source venv/bin/activate
```

#### 2.3 Install Dependencies
Install Django and other dependencies using requirements.txt:
```bash
pip install -r requirements.txt
```

#### 2.4 Start the Django Server
``` bash
python manage.py runserver
```

### 3. Set Up the Frontend (Next.js)
#### 3.1 Install npm Packages
In the frontend folder, install the frontend dependencies:

``` bash
cd ../frontend
npm install
```

#### 3.2 Start the Next.js Development Server
``` bash
npm run dev
```

### Accessing the Application
- Backend API: http://127.0.0.1:8000
- Frontend Application: http://localhost:5173/

### Contact
If you have any questions or need further information, feel free to reach out:

- Email: wuyanjie.jason@gmail.com
- Phone: (+61) 476 217 002

### License
This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).