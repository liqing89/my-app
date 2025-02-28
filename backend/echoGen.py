import numpy as np
import os
from joblib import Parallel, delayed
import scipy.io as sio
# import matplotlib.pyplot as plt
from scipy.signal import windows
import math
import plotly.express as px

def calSquiAngOff(sat2pt, beamDir):
    cos_angle = np.dot(sat2pt, beamDir) / (np.linalg.norm(sat2pt) * np.linalg.norm(beamDir))
    return np.arccos(cos_angle) * 180 / np.pi

def airbone_echo_gen(tags=None, delta_h=0):
    if tags is None:
        tags = {
            'date': '0225',
            'model': "TEST",
            'saveFlag': 1,
            'simScene': 1,
            'echofolder': "./echoGenResult/",
            'isDualFreq': 0
        }

    date = tags['date']
    model = tags['model']
    save_flag = tags['saveFlag']
    sim_scene = tags['simScene']

    save_folder = os.path.join(tags['echofolder'], date)
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    save_echo_path = os.path.join(save_folder, f"{model}at{delta_h}m.npy")

    fc = 15.2e9
    theta_ref = 45
    Rnc = 500
    theta_rc = 0
    x_scale = 200
    y_scale = 200

    if model == "TEST":
        data1 = np.array([
            [-50, 50, 0, 10], [0, 50, 0, 10], [50, 50, 0, 10],
            [-50, 0, 0, 10], [0, 0, 0, 10], [50, 0, 0, 10],
            [-50, -50, 0, 10], [0, -50, 0, 10], [50, -50, 0, 10]
        ])
    else:
        data = sio.loadmat(f"./eleResult/{model}_eleResult.mat")['data']
        data1 = np.hstack([-data[:, 1:2], data[:, 0:1], data[:, 2:3], data[:, 3:4]])

    if sim_scene == 0:
        off_nadi_ang = theta_ref
        data = data1 + np.array([-np.tan(np.deg2rad(off_nadi_ang)) * delta_h, 0, 0, 0])
    elif sim_scene == 1:
        off_nadi_ang = theta_ref
        data = data1.copy()
    elif sim_scene == 2:
        Rnc_prime = np.sqrt(delta_h**2 + Rnc**2)
        off_nadi_ang = np.rad2deg(np.arccos((Rnc * np.cos(np.deg2rad(theta_ref)) + delta_h * np.sin(np.deg2rad(theta_ref))) / Rnc_prime))
        data = data1.copy()
    data1 = None

    c = 3e8
    lamda = c / fc
    azm_rho = 1
    rng_rho = 1
    Tp = 1e-6
    B = 1200e6
    Kr = B / Tp
    fs = 1.2 * B
    V = 10
    fdop = V / azm_rho
    PRF = 1.3 * fdop
    theta_bw = fdop * lamda / (2 * V * np.cos(theta_rc))
    look_side = 1
    antenna_mode = -1
    rise_ratio = 16

    if sim_scene == 0:
        R0 = Rnc * np.cos(theta_rc)
        radar_h = R0 * np.cos(np.deg2rad(off_nadi_ang))
        radar_x = R0 * np.sin(np.deg2rad(off_nadi_ang)) * (-look_side)
    elif sim_scene == 1:
        R0 = Rnc + delta_h * np.tan(np.deg2rad(off_nadi_ang))
        radar_h = R0 * np.cos(np.deg2rad(off_nadi_ang))
        radar_x = R0 * np.sin(np.deg2rad(off_nadi_ang)) * (-look_side) + delta_h / np.cos(np.deg2rad(off_nadi_ang))
    elif sim_scene == 2:
        R0 = np.sqrt(delta_h**2 + Rnc**2) * np.cos(theta_rc)
        radar_h = R0 * np.cos(np.deg2rad(off_nadi_ang))
        radar_x = R0 * np.sin(np.deg2rad(off_nadi_ang)) * (-look_side)

    Ls = theta_bw * Rnc / np.cos(theta_rc)
    L = Ls + y_scale
    L = math.ceil(L / (V/PRF) / 2) * 2 * V / PRF
    radar_yc = -Rnc * np.sin(theta_rc)
    sat_track_y = np.arange(-L/2, L/2 + V/PRF, V/PRF) + radar_yc
    sample_num = len(sat_track_y)

    sat_track_ideal = np.vstack([
        np.full(sample_num, radar_x),
        sat_track_y,
        np.full(sample_num, radar_h)
    ])
    sat_track = sat_track_ideal.copy()

    beam_dir = -np.array([[radar_x], [radar_yc], [radar_h]])
    beam_dir /= np.linalg.norm(beam_dir)
    beam_dir = np.tile(beam_dir, (1, sample_num))

    Ts = 1 / fs / rise_ratio
    t = np.arange(-Tp/2, Tp/2, Ts)
    sig = np.exp(1j * np.pi * Kr * t**2)
    rng_interv = Ts * c / 2
    rise_nr = len(t) + int((Rnc*2 - Rnc*0.8) / rng_interv)
    Nr = int(rise_nr / rise_ratio)
    sig_fft = np.fft.fft(sig, rise_nr)

    pt_pos = data[:, :3].T
    N = pt_pos.shape[1]
    np.random.seed(1)
    rcs_vec = data[:, 3] * np.exp(1j * (2 * np.pi * np.random.randn(N) - np.pi))

    echo_data = np.zeros((sample_num, Nr), dtype=np.complex128)

    def process_sample(i):
        rng_line = np.zeros(rise_nr, dtype=np.complex128)
        sat_pos = sat_track[:, i]
        sat2pt_all = pt_pos - sat_pos.reshape(-1, 1)
        Rk_all = np.linalg.norm(sat2pt_all, axis=0)
        valid_range_idx = np.round((Rk_all - Rnc*0.8) / rng_interv).astype(int)
        valid_range = (valid_range_idx >= 0) & (valid_range_idx < rise_nr)

        squi_ang_off = np.array([calSquiAngOff(sat2pt_all[:,k], beam_dir[:,i]) for k in range(N)])
        valid_angle = np.abs(squi_ang_off) <= theta_bw/2
        valid_points = valid_range & valid_angle

        for k in np.where(valid_points)[0]:
            if antenna_mode == 1:
                A = 1
            else:
                A = np.sinc(squi_ang_off[k] / theta_bw)**2
            phase = -1j * 4 * np.pi * Rk_all[k] / lamda
            rng_line[valid_range_idx[k]] += A * rcs_vec[k] * np.exp(phase)

        rng_line_fft = np.fft.fft(rng_line) * sig_fft
        return np.fft.ifft(rng_line_fft)[::rise_ratio]

    echo_data = np.array(Parallel(n_jobs=10)(delayed(process_sample)(i) for i in range(sample_num)))

    # plt.figure()
    # plt.imshow(np.abs(echo_data))
    # plt.title('Original Echo')
    # plt.show()

    # fig = px.imshow(np.abs(echo_data), color_continuous_scale="Viridis", labels={"x": "X轴", "y": "Y轴"})
    # fig.update_layout(title="Plotly 回波图像")
    # fig.show()

    print("here!");

    if save_flag:
        params = {
            'data': echo_data,
            'satTrack': sat_track,
            'c': c,
            'fc': fc,
            'lamda': lamda,
            'fs': fs,
            'Tp': Tp,
            'Kr': Kr,
            'B': B,
            'PRF': PRF,
            'V': V,
            'delta_h': delta_h,
            'offNadiAng': off_nadi_ang,
            'rngStart': Rnc*0.8,
            'rngEnd': Rnc*2,
            'theta_bw': theta_bw,
            'xScale': x_scale,
            'yScale': y_scale,
            'R0': R0,
            'Rnc': Rnc,
            'lookSide': look_side
        }
        np.save(save_echo_path, data, allow_pickle=True)

    # if save_flag:
    #     sio.savemat(save_echo_path, {
    #         'data': echo_data,
    #         'satTrack': sat_track,
    #         'c': c,
    #         'fc': fc,
    #         'lamda': lamda,
    #         'fs': fs,
    #         'Tp': Tp,
    #         'Kr': Kr,
    #         'B': B,
    #         'PRF': PRF,
    #         'V': V,
    #         'delta_h': delta_h,
    #         'offNadiAng': off_nadi_ang,
    #         'rngStart': Rnc*0.8,
    #         'rngEnd': Rnc*2,
    #         'theta_bw': theta_bw,
    #         'xScale': x_scale,
    #         'yScale': y_scale,
    #         'R0': R0,
    #         'Rnc': Rnc,
    #         'lookSide': look_side
    #     })
    #     return 1

    print("return!")

    return 0

if __name__ == "__main__":
    airbone_echo_gen()