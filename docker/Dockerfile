FROM python:3.12.7

RUN pip install --upgrade pip
RUN pip3 install openai
RUN pip3 install xlsxwriter
RUN pip3 install flask
RUN pip3 install bs4
RUN pip3 install flasgger
RUN pip3 install flask_limiter
RUN pip3 install flask_cors
RUN pip3 install gunicorn
RUN pip3 install prometheus_client
RUN pip3 install vertexai

WORKDIR /faqbot
COPY app app
COPY cfg cfg
COPY prompts prompts

ENV PYTHONPATH=/faqbot/app:$PYTHONPATH

ENTRYPOINT ["gunicorn","app.main:create_rest_app()"]
CMD ["-w", "1", "--threads", "5", "--timeout", "120", "-b", "0.0.0.0:8080"]

EXPOSE 8080
EXPOSE 5000