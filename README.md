# Harmony Backend

## Setup

1. (Optional) Create and activate a virtual environment.
2. Install the project dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

The project exposes an application factory via the `harmony` package. You can
start the Socket.IO enabled development server directly with:

```bash
python app.py
```

If you prefer using Flask's CLI, set the `FLASK_APP` environment variable to
`"harmony:create_app"` before running `flask run`.
 
