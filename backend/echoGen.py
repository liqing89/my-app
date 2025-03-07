import numpy as np
import matplotlib.pyplot as plt
import os
import scipy.io as sio
from numpy.fft import fft, ifft
import multiprocessing
import cupy as cp

import time

def AirboneEchoGen(tags, params, delta_h=0):

    # 基本参数
    fc = params["fc"]  # P波段

    # 文件接口
    date = tags['date']
    model = tags['model']
    saveFlag = tags['saveFlag']
    simScene = tags['simScene']

    thetaRef = params["theta"] # 主图像下视角
    Rnc = params["R0"] # 主图像景中心斜距
    theta_rc = 0 / 180 * np.pi # 斜视角

    # 平地区域场景大小
    xScale = 300
    yScale = 300

    # 数据存储路径
    saveFolder = os.path.join(tags['echofolder'], date)
    if not os.path.exists(saveFolder):
        os.makedirs(saveFolder)

    saveEchoPath = os.path.join(saveFolder, f"{model}at{delta_h}m.mat")

    # 导入建模数据
    if model == "TEST":
        data1 = np.array([
            [0, 0, 0, 10]
        ])
    else:
        data = sio.loadmat(f"./eleResult/{model}_eleResult.mat")
        data1 = np.array([data['data'][:, 1], data['data'][:, 0], data['data'][:, 2], data['data'][:, 3]]).T

    # 层析向基线分布选择
    if simScene == 0:
        offNadiAng = thetaRef
        data = data1 + np.array([-np.tan(np.deg2rad(offNadiAng)) * delta_h, 0, 0, 0])
    elif simScene == 1:
        offNadiAng = thetaRef
        data = data1
    elif simScene == 2:
        offNadiAng = np.arccos((Rnc * np.cos(np.deg2rad(thetaRef)) + delta_h * np.sin(np.deg2rad(thetaRef))) /
                               np.sqrt(delta_h**2 + Rnc**2))
        data = data1

    c = 3e8
    lamda = c / fc
    azmRho = 1.5
    rngRho = 1.5
    Tp = params["Tp"]

    B = params["B"] # B = c / (2 * rngRho)
    Kr = B / Tp
    fs = params["fs"] # fs = 1.2 * B

    V = params["Vg"]
    fdop = params["fdop"]   # fdop = V / azmRho
    PRF = params["PRF"]  # PRF = 1.3 * fdop

    theta_bw = fdop * lamda / (2 * V * np.cos(theta_rc))

    lookSide = 1
    antennaMode = -1
    riseRatio = 16

    # 斜视影响的计算
    if simScene == 0:
        Rnc = Rnc + delta_h / np.cos(np.deg2rad(offNadiAng))
        R0 = Rnc * np.cos(theta_rc)
        radarH = R0 * np.cos(np.deg2rad(offNadiAng))
        radarX = R0 * np.sin(np.deg2rad(offNadiAng)) * (-lookSide)
    elif simScene == 1:
        R0 = Rnc + delta_h * np.tan(np.deg2rad(offNadiAng))
        radarH = R0 * np.cos(np.deg2rad(offNadiAng))
        radarX = R0 * np.sin(np.deg2rad(offNadiAng)) * (-lookSide) + delta_h / np.cos(np.deg2rad(offNadiAng))
    elif simScene == 2:
        R0 = np.sqrt(delta_h**2 + Rnc**2) * np.cos(theta_rc)
        radarH = R0 * np.cos(np.deg2rad(offNadiAng))
        radarX = R0 * np.sin(np.deg2rad(offNadiAng)) * (-lookSide)

    # 合成孔径长度和方位向采样
    Ls = theta_bw * Rnc / np.cos(theta_rc)
    L = Ls + yScale
    L = np.ceil(L / (V / PRF) / 2) * 2 * V / PRF
    radarYc = -Rnc * np.sin(theta_rc)
    satTrackY = np.linspace(-L / 2, L / 2, int(L / (V / PRF)) + 1) + radarYc
    sampleNum = len(satTrackY)

    satTrackIdeal = np.vstack([np.ones(sampleNum) * radarX, satTrackY, np.ones(sampleNum) * radarH])
    satTrack = satTrackIdeal

    # 波束宽度
    beamDir = -np.array([radarX, radarYc, radarH])
    beamDir = beamDir / np.linalg.norm(beamDir)
    beamDir = np.tile(beamDir[:, np.newaxis], (1, sampleNum))

    # 波门开关
    radarH_ref = Rnc * np.cos(np.deg2rad(thetaRef))
    radarX_ref = Rnc * np.sin(np.deg2rad(thetaRef)) * (-lookSide)
    rngStart = np.sqrt((np.abs(radarX_ref)-xScale/2)**2 + radarH_ref**2)     # 场景最近斜距
    rngEnd = np.sqrt((R0*np.tan(np.abs(theta_rc)+theta_bw/2))**2 + (np.abs(radarX_ref)+xScale/2)**2 + radarH_ref**2)

    Ts =  1/fs/riseRatio
    t = np.arange(-Tp/2, Tp/2, Ts)
    sig = np.exp(1j*np.pi*Kr*t**2)
    rngInterv = Ts*c/2
    riseNr = np.round(Tp/Ts) + np.round((rngEnd-rngStart)/rngInterv)
    riseNr = int(np.ceil(riseNr/riseRatio)*riseRatio)
    Nr = int(riseNr/riseRatio)
    sigFFT = np.fft.fft(sig, int(riseNr))


    ptPos = data[:, 0:3].T
    N = ptPos.shape[1]
    np.random.seed(1)
    rcsVec = data[:, 3].T * np.exp(1j * (2 * np.pi * np.random.randn(1, N) - np.pi))
    constExp = -1j*4*np.pi/lamda

    echoData = cp.zeros((int(sampleNum), int(Nr)), dtype=complex)

    for i in range(sampleNum):
        rngLine = cp.zeros(int(riseNr), dtype=complex)
        sat2ptAll = cp.array(ptPos) - cp.array(satTrack[:, i]).reshape(-1, 1)
        Rk_all = cp.linalg.norm(sat2ptAll, axis=0)

        squiAngOff_all = cp.zeros(N)
        for k in range(N):
            beamDir_cp = cp.array(beamDir)
            numerator = cp.dot(sat2ptAll[:, k], beamDir_cp[:, i])
            denominator = cp.linalg.norm(sat2ptAll[:, k]) * cp.linalg.norm(beamDir[:, i])
            squiAngOff_all[k] = cp.arccos(numerator / denominator)

        valid_range_idx = cp.round((Rk_all - rngStart) / rngInterv).astype(cp.int32)
        valid_range_idx = cp.clip(valid_range_idx, 0, len(rngLine) - 1)
        valid_range = (valid_range_idx >= 0) & (valid_range_idx < riseNr)
        valid_angle = cp.abs(squiAngOff_all) <= theta_bw / 2
        valid_points = valid_range & valid_angle

        valid_indices = cp.where(valid_points)[0]
        for k in valid_indices.get():
            rngIdx = int(valid_range_idx[k].item())
            if antennaMode == 1:
                A = 1
            else:
                A = cp.sinc(squiAngOff_all[k] / theta_bw) ** 2
            if 0 <= rngIdx < len(rngLine):
                rngLine[rngIdx] += A * rcsVec[k].item() * cp.exp(constExp * Rk_all[k].item())
            else:
                print(f"Invalid index {rngIdx}, skipping this iteration.")

        rngLine = cp.fft.ifft(cp.fft.fft(rngLine) * cp.asarray(sigFFT))
        echoData[i, :] = rngLine[::riseRatio]

    echodata = cp.asnumpy(echoData)

    # 保存结果
    if saveFlag == 1:
        sio.savemat(saveEchoPath, {'data': echodata, 'satTrack': satTrack, 'c': c, 'fc': fc, 'lamda': lamda, 'fs': fs, 'Tp': Tp, 'Kr': Kr, 'B': B, 'PRF': PRF, 'V': V, 'delta_h': delta_h, 'offNadiAng': offNadiAng})

    output_folder = './pltResult'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    plt.imshow(np.abs(echodata), aspect='auto')
    plt.title('Orinial Echo')
    plt.show()
    plt.savefig(f"{output_folder}/plot.png", format="png")
    # plt.close() # 关闭当前图像以释放内存

    return 1

if __name__ == "__main__":
    start_time = time.time()

    tags = {
        'date':'0306',
        'model':'TEST',
        'saveFlag':1,
        'simScene':1,
        'echofolder':'./echoGenResult/',
        'isDualFreq':0
    }
    params = {
        'fc':400e6,
        'theta': 71.8547,  # 示例值
        'R0': 700,   # 示例值
        'Tp': 4e-6,
        'B': 300e6,
        'fs': 400e6,
        'Vg': 10,
        'fdop': 20,
        'PRF': 40
    }
    AirboneEchoGen(tags,params)
    end_time = time.time()
    print("计算用时: {:.3f} 秒".format(end_time - start_time))