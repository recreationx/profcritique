# RapportCard
This was done for National AI Challenge 2022.

See attached write-up for more information.

## Setting Up
You require the following packages (all avaiable via `pip`)
- Python 3.10.7
- SQLite
- WTForms
- Flask
- Flask-Login
- SGNlp

Using the following command:
```bash
pip install -r requirements.txt
```

Then run with any command line of your choice,
```bash
python main.py
```
An instance of the site will start running at `127.0.0.1:5000`.

## Testing
Two existing users, `admin` and `student` are already included in the database `test.db`. You can log in to them via the demo.

## Program structure
- `prototype` contains the training and testing dataset, together with `model.py`, responsible for handling the prediction of the model
- `static` and `templates` includes site pages and assets
- `utils` include the associated componments (handling of SQLite database, forms etc.)
- `test.db` is the developmental database. We use this for testing.