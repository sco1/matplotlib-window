from matplotlib_window.window import fixed_window

x_data = y_data = list(range(6))

bounds = fixed_window(
    x_data=x_data,
    y_data=y_data,
    position=2,
    window_width=2,
)
print(bounds)
