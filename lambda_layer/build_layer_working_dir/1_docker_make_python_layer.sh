docker run --rm -v $(pwd):/foo -w /foo lambci/lambda:build-python3.8 \
    pip install -r ./temp/requirements.txt -t ./temp/python
