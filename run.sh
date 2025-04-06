cd backend
source myenv/bin/activate
export PYTHONPATH=$PYTHONPATH:/root/nbackend
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8010
