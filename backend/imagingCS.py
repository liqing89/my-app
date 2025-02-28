import numpy as np
import os
from scipy.io import loadmat, savemat

def CS(tags=None, delta_h=0):
    # 处理默认参数
    if tags is None:
        tags = {
            'date': "0225",
            'model': "TEST",
            'saveFlag': 1,
            'loadFlag': 1,
            'imgfolder': "./imagingResult",
            'isDualFreq': 1,
            'method': "CS"
        }

    # 读取回波数据
    model = tags['model']
    date = tags['date']
    method = tags['method']
    saveFlag = tags['saveFlag']
    loadFlag = tags['loadFlag']

    if loadFlag != 0:
        # data = loadmat(f"./echoGenResult/{date}/{model}at{delta_h}m.mat")['data']
        np.load(f"./echoGenResult/{date}/{model}at{delta_h}m.npy", allow_pickle=True)

    print("test");

    # 创建保存目录
    if saveFlag != 0:
        save_folder = f"./imagingResult/{method}{date}/"
        os.makedirs(save_folder, exist_ok=True)
        save_path = f"{save_folder}{model}at{delta_h}m.mat"

    # 获取矩阵维度
    Na, Nr = data.shape

    # 假设以下参数已在工作区定义
    rngStart = 0      # 替换实际值
    c = 3e8           # 光速
    fs = 1e6          # 采样率
    Tp = 1e-6         # 脉冲宽度
    Rnc = 1000        # 参考距离
    V = 100           # 平台速度
    lamda = 0.03      # 波长
    fc = 10e9         # 中心频率
    PRF = 2000        # 脉冲重复频率
    Kr = 1e12         # 调频率

    # 距离变标处理
    tr = 2*rngStart/c + (np.arange(Nr)/fs) - Tp/2
    Rref = Rnc
    fdc = 0

    fa = np.linspace(-PRF/2, PRF/2-PRF/Na, Na) + fdc
    fa = np.roll(fa, -int(Na/2 - fdc/PRF*Na))

    D = np.sqrt(1 - (lamda**2 * fa**2)/(4*V**2))
    Dref = np.sqrt(1 - (lamda**2 * fdc**2)/(4*V**2))

    Ksrc = (2 * V**2 * fc**3 * D**3) / (c * Rref * fa**2)
    Km = Kr / (1 - Kr/Ksrc)

    Ssc = np.zeros((Na, Nr), dtype=np.complex128)
    for i in range(Na):
        phase = np.pi * Km[i] * (Dref/D[i] - 1) * (tr - 2*Rref/(c*D[i]))**2
        Ssc[i, :] = np.exp(1j * phase)

    S1 = np.fft.fft(data, axis=0)
    S1 *= Ssc
    S1 = np.fft.fft(S1, axis=1)

    # 频域处理
    fr = np.fft.fftshift(np.linspace(-fs/2, fs/2-fs/Nr, Nr))

    H1 = np.exp(1j * np.pi * D[:, None]/Km[:, None]/Dref * fr**2)
    H2 = np.exp(1j * 4*np.pi*Rref/c * (1/D[:, None] - 1/Dref) * fr)
    S2 = S1 * H1 * H2

    H3 = np.exp(1j * 4*np.pi*(Rref/Dref - Rref)/c * fr)
    S2 *= H3
    S2 = np.fft.ifft(S2, axis=1)

    # 方位压缩处理
    Rn = rngStart + (np.arange(Nr)/fs - Tp/2)*c/2
    H3 = np.exp(1j * 4*np.pi*fc/c * D[:, None]*Rn)
    H4 = np.exp(-1j * 4*np.pi*Km[:, None]/c**2 * (1/D[:, None] - 1/Dref) * (Rn/D[:, None] - Rref/Dref)**2)

    S3 = S2 * H3 * H4 * np.exp(-1j * 4*np.pi*Rn/lamda)
    img = np.fft.ifft(S3, axis=0)

    # 保存结果
    if saveFlag != 0:
        savemat(save_path, {'img': img})

    return img


if __name__ == "__main__":
    CS()