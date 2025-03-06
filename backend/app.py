from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from fontTools.ttLib.tables.otTables import DeltaSetIndexMap
import os
import json

# sys.path.append(os.path.dirname(__file__))
from echoGen import AirboneEchoGen

app = Flask(__name__)
CORS(app)  # 解决跨域问题

@app.route('/api/echoGen', methods=['POST'])
def getEchoData():
    params = request.get_json()
    # params = json.loads(params)
    for key, value in params.items():
        try:
            # 如果是数字字符串，就转换为 f6loat
            params[key] = float(value)
        except ValueError:
            # 如果转换失败（即不是有效的数字），保持原值
            continue
    # fc = float(params["fc"])
    # test = fc/2
    # print(test)
    print(params)
    tags = {
        'date':'0305',
        'model':'TEST',
        'saveFlag':1,
        'simScene':1,
        'echofolder':'./echoGenResult/',
        'isDualFreq':0
    }
    result = AirboneEchoGen(tags,params)
    if result == 1:
        return jsonify({"message": "Echo Data saved!"})
    else:
        return jsonify({"message": "Echo Data not saved."})


# 设置静态文件路径
app.config['PLT_RESULT_FOLDER'] = './pltResult'
@app.route('/pltResult/<filename>')
def serve_plot(filename):
    return send_from_directory(app.config['PLT_RESULT_FOLDER'], filename)


@app.route('/api/calRes', methods=['POST'])
def calRes():
    data = request.get_json()
    c = 3e8
    bw = float(data.get("B", -1))
    fdop = float(data.get("fdop", -1))
    Vg = float(data.get("Vg", -1))
    if (bw != -1 and fdop != -1 and Vg != -1):
        range_res = c/2/bw
        azi_res = Vg/fdop
        return jsonify({"rangeRes":str(range_res), "aziRes":azi_res})
    elif (bw != -1 and (fdop == -1 or Vg == -1)):
        range_res = c/2/bw
        return jsonify({"rangeRes":range_res, "aziRes":0})
    elif  (bw == -1 and (fdop != -1 and Vg != -1)):
        azi_res = Vg/fdop
        return jsonify({"rangeRes":0, "aziRes":azi_res})
    else:
        return jsonify({"rangeRes":0, "aziRes":0})


if __name__ == '__main__':
    app.run(debug=True, port=5000)