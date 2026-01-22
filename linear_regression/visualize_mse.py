import matplotlib.pyplot as plt 

def plot_mse(mse_train, mse_test):
    plt.figure(figsize=(10,4))
    plt.title("Learning curve")
    plt.plot(mse_train, label ="train")
    plt.plot(mse_test, label="test")
    plt.legend()

    plt.xlabel("iterations", fontsize = 12)
    plt.ylabel("MSE Loss", fontsize=12)

    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    mse_train = [0.5, 0.4, 0.3, 0.2, 0.15]
    mse_test = [0.6, 0.5, 0.4, 0.35, 0.3]
    plot_mse(mse_train, mse_test)