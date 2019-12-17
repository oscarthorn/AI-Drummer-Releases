import os, time, json
import multiprocessing as mp
from flask import Flask, request
from redis import Redis
from rq import Queue, get_current_job
from rq.exceptions import NoSuchJobError
from rq.job import Job
from Fuzzy.output_interface import OutputInterface


ALLOWED_EXTENSIONS = {'mid'}
UPLOAD_FOLDER = './Server/uploads/'
PORTS_STRIKE = {'NuJazz': 'I Strike_Nu_Jazz', 'JazzBossa': 'I Strike_Jazz_Bossa',
                'BrushesSwing': 'I Strike_b_swing', 'BossaBrushes': 'I Strike_bo_brushes'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/start", methods=['POST'])
def start():

    if request.method == 'POST':
        mode = request.form.get('mode')
        play_instrument = request.form.get('play_instrument')
        style = request.form.get('style')
        customRulesDict = request.form.get('custom_rules')

        if mode is None:
            return 'Failed, mode is none {}'.format(request.args)

        if style is None:
            return 'Failed, style is none'

        if style in PORTS_STRIKE.keys():
            strike_port = PORTS_STRIKE[style]
        else:
            return 'Failed, bad style'

        if customRulesDict is not None:
            customRulesDict = json.loads(customRulesDict)

        if mode == 'live':
            args = {
                'mode': mode,
                'play_instrument': play_instrument,
                'out_port': strike_port,
                'instrument_port': 'I Piano_out',
                'in_port': 'Scarlett 18i8 USB',
                'custom_rules': customRulesDict
            }

        elif mode == 'playback':
            # check if the post request has the file part
            if 'file' not in request.files:
                return 'Failed, no file in request.files'
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                return 'Failed, empty filename'
            if file and allowed_file(file.filename):
                filename = file.filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(os.path.join(file_path))
                file.close()
            else:
                return 'Failed, failed to save file'
            args = {
                'mode': mode,
                'play_instrument': play_instrument,
                'file': file_path,
                'out_port': strike_port,
                'instrument_port': 'I Piano_out',
                'custom_rules': customRulesDict
            }
        else:
            return 'Failed, bad mode'

        redis_conn = Redis()
        q = Queue(connection=redis_conn)
        job = q.enqueue(start_job, args, job_id='strike')
        job.meta['stop'] = False
        job.save_meta()
    else:
        return 'Request should be post'
    return 'Done'


def start_job(args):
    job = get_current_job()
    proc = mp.Process(target=run, args=(args,))
    proc.start()
    while proc.is_alive():
        job.refresh()
        time.sleep(1)
        if job.meta['stop']:
            proc.kill()


def run(args):
    from Fuzzy.aidrummer import AiDrummer
    d = AiDrummer(**args)
    d.run()


@app.route("/stop")
def stop():
    redis = Redis()
    try:
        job = Job.fetch('strike', connection=redis)
    except NoSuchJobError:
        return 'No job to stop'
    job.meta['stop'] = True
    job.save_meta()
    for port in PORTS_STRIKE:
        OutputInterface(PORTS_STRIKE[port])   # Runs a reset on the port
    return 'All stopped'


@app.route("/test")
def test():
    return "Server is live, and ready to make some music!"


if __name__ == "__main__":
    app.run(host='0.0.0.0')
