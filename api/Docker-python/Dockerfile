# Sử dụng một hình ảnh Python chính thức làm hình cơ sở
FROM python:3.10.12

# Đặt thư mục làm thư mục làm việc
WORKDIR /app

# Tạo thư mục /app nếu nó chưa tồn tại
RUN mkdir -p /app

RUN pip install --upgrade pip 
# Cài đặt virtualenv và các gói cần thiết
RUN pip install virtualenv

# Tạo thư mục cho virtualenv và chuyển đến thư mục đó
RUN mkdir -p /app/venv
WORKDIR /app/venv

# Tạo môi trường ảo với python3
RUN virtualenv -p python3 .

# Kích thích môi trường ảo
RUN . /app/venv/bin/activate

# Chuyển đến thư mục làm việc chính
WORKDIR /app

# Copy requirements.txt vào /app
COPY requirements.txt /app/

# Cài đặt các thư viện từ requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy tất cả các tệp trong thư mục hiện tại vào /app
COPY . /app/

# Mở cổng 8000 để có thể truy cập ứng dụng từ bên ngoài container
EXPOSE 8000

# Sử dụng Gunicorn để chạy ứng dụng Flask
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app.wsgi:app"]

