import matplotlib.pyplot as plt
from matplotlib import dates as md
from matplotlib import rcParams


def plot_statistics(df, players):
    """Рисует картинку statistics.png на основе данных в statistics.csv."""
    rcParams['font.family'] = 'sans-serif'
    rcParams['font.size'] = 8

    fig = plt.figure(figsize=(10, 8))
    # Расстояние между графиками
    fig.subplots_adjust(hspace=0.15)

    # Bar Chart settings
    x_labels = [players[int(x)][1] for x in df.columns[3:]]
    ax1 = fig.add_subplot(211)
    ax1.set_title(df.iloc[-1, 0].strftime("%Y/%m/%d %H:%M:%S"))
    ax1.grid(True, linestyle='dotted', axis='y')
    ax1.set_xlabel('PLAYERS')
    ax1.set_ylabel('WINS')

    colors = ['#2ca02c', '#ff7f0e', '#1f77b4', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    hatches = []

    y = df.iloc[-1, 3:]
    y_min, y_max = y.min(), y.max()
    for val in y:
        if val == y_max:
            # colors.append('green')
            hatches.append('*')
        elif val == y_min:
            # colors.append('red')
            hatches.append('o')
        else:
            # colors.append('#827717')
            hatches.append(None)

    # Line Chart Settings
    ax2 = fig.add_subplot(212)
    ax2.grid(which='both', linestyle='dotted')
    ax2.set_xlabel('GAME DATES')
    ax2.set_ylabel('WINS')
    ax2.legend(x_labels)
    ax2.xaxis.set_major_formatter(md.DateFormatter('%Y/%m/%d\n%H:%M'))

    # Plot
    ax1.bar(x_labels, y, width=0.4, color=colors, hatch=hatches, edgecolor='black')
    for i in range(len(df.columns) - 3):
        ax2.plot(df['datetime'], df.iloc[:, i + 3], marker='o', linestyle='-', markerfacecolor='none', color=colors[i])

    fig.savefig('statistics_data/statistics.png', dpi=300, bbox_inches='tight')
