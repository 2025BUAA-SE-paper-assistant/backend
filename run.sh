# 检查 tmux 会话是否存在，如果不存在则创建
tmux has-session -t my_terminal 2>/dev/null || tmux new-session -d -s my_terminal

cd backend
source myenv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate

# 停止现有的 runserver 进程（无需 sudo）
pkill -f "python manage.py runserver" || true

# 使用 tmux 在后台运行 Django 服务
tmux new-session -d -s my_terminal "python manage.py runserver 0.0.0.0:8010"
