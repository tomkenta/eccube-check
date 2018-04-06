from flask import Flask, render_template, request
import subprocess, os

app = Flask(__name__)
cart_path = os.path.dirname(os.path.abspath(__file__)) + "/scraper/cart_check.py"


class NPWebCartChecker:
    title = 'NP Web Cart Checker'


@app.route('/')
def index():
    return render_template('index.html', title=NPWebCartChecker.title)


@app.route('/sendtext', methods=['POST'])
def sendtext():
    url = request.form['url']

    # cmd = 'python {path} -u {url}'.format(path=cart_path, url=url)
    cmd = ['python', cart_path, '-u', url]
    #   output = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
    print(cmd)
    try:
        output = subprocess.check_output(cmd)
    except:
        print("Error.")
        import traceback
        traceback.print_exc()

    return render_template('index.html', title=NPWebCartChecker.title)



if __name__ == "__main__":
    app.run(debug=True)
