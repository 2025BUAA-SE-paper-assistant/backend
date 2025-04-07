tmux attach -t my_terminal  # 恢复会话
cd backend
source myenv/bin/activate
# export PYTHONPATH=/usr/zjq/backend/backend
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
sudo pkill -f "python manage.py runserver"
python manage.py runserver 0.0.0.0:8010
