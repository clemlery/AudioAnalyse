import io
import base64
import urllib.parse

import matplotlib.pyplot as plt


def fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return encoded


def df_to_csv_uri(df) -> str:
    csv = df.to_csv(index=False)
    return "data:text/csv;charset=utf-8," + urllib.parse.quote(csv)
