import sys
from pathlib import Path
import urllib.request
import pandas
import numpy as np
import matplotlib.pyplot as plt

from data import generate_data, prepare_data
from model import gradient_descent

from sklearn.preprocessing import StandardScaler

INTERACTIVE_URL = (
    "https://edunet.kea.su/repo/EduNet_NLP-web_dependencies/L02/"
    "interactive_visualization.py"
)

def plot_mse(mse_train, mse_test):
    plt.figure(figsize=(10, 4))
    plt.title("Learning curve")
    plt.plot(mse_train, label="train")
    plt.plot(mse_test, label="test")
    plt.legend()

    plt.xlabel("iterations", fontsize=12)
    plt.ylabel("MSE Loss", fontsize=12)

    plt.grid(True)
    plt.show()

def ensure_interactive_module(target_dir: Path) -> bool:
    module_path = target_dir / "interactive_visualization.py"

    if module_path.exists():
        print(f" Module alrady exist: {module_path}")
        return
    
    print(f"Module download from {INTERACTIVE_URL}...")
    try:
        urllib.request.urlretrieve(INTERACTIVE_URL, module_path.as_posix())
        if module_path.exists() and module_path.stat().st_size > 0:
            print(f"The module has already been downloaded: ({module_path.stat().st_size} bytes)")
            return True
        else:
            print(f"File is empty or not create")
            return False
    except Exception as exc:
        print(f"Warning: could not download interactive module: {exc}")
        return False

def load_interactive_plot():
    script_dir = Path(__file__).resolve().parent

    if not ensure_interactive_module(script_dir):
        print("Could not download interactive module. Please check your internet connection and try again.")
        return None

    module_path = script_dir / "interactive_visualization.py"
   
    if not module_path.exists():
        print(f"The file not found: {module_path}")
        return None

    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
        print(f"Add in sys.path: {script_dir}")

    try:
        from interactive_visualization import plot_grid_search_2d
    except Exception as exc:
        print(f"Warning: could not import interactive module: {exc}")
        return None

    return plot_grid_search_2d

def main():
    x, y = generate_data(n=1000, noise=0.8)
    x_train, x_test, y_train, y_test = prepare_data(x, y)

    y_train = y_train.ravel()
    y_test = y_test.ravel()

    scaler = StandardScaler()

    x_train_scaled = scaler.fit_transform(np.expand_dims(x_train[:, 1], axis=1)).flatten()
    x_test_scaled = scaler.transform(np.expand_dims(x_test[:, 1], axis=1)).flatten()

    x_train_with_bias = np.column_stack([np.ones(len(x_train_scaled)), x_train_scaled])
    x_test_with_bias = np.column_stack([np.ones(len(x_test_scaled)), x_test_scaled])

    plot_grid_search_2d = load_interactive_plot()

    if plot_grid_search_2d is not None:
        print("\n🎨 Visualization of the search space (before training)...")
        intercepts = np.arange(-15, 25, 0.2)
        slopes = np.arange(-20, 20, 0.2)
        plot_grid_search_2d(x_train_scaled, y_train, slopes, intercepts)
    else:
        print("⚠️  Interactive visualization is not available")

    w_init = np.array([[0.0], [0.0]])
    w, mse_train, mse_test = gradient_descent(
        x_train,
        y_train,
        x_test,
        y_test,
        w_init,
        alpha=0.05,
        iterations=800,
    )

    print(f"\nFinal weights: bias = {w[0, 0]:.4f}, slope = {w[1, 0]:.4f}")

    plot_mse(mse_train, mse_test)
    
    if plot_grid_search_2d is None:
        print("⚠️  Interactive visualization is not available")
        return
        
    intercepts = np.arange(-7.5, 12.5, 0.1)
    slopes = np.arange(-5, 5, 0.1)
    plot_grid_search_2d(x_train_scaled, y_train, slopes, intercepts)

    b = ws[-1][0] - ws[-1][1] * scaler.mean_ / (scaler.var_) ** 0.5
    w = ws[-1][1] / (scaler.var_) ** 0.5

    print(f"y = {w[0]:.2f}x + {b[0]:.2f}")

    plot_gradient_descent_2d(
        x_train_scaled[:, 1],
        y_train[:, 0],
        ws,
        slopes,
        intercepts,
    )

if __name__ == "__main__":
    main()