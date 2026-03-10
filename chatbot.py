from flask import Flask, render_template, request

app = Flask(__name__)

responses = {
    "fee": "The B.Tech fee is ₹75,000 per year.",
    "admission": "Admissions start in June every year.",
    "course": "We offer B.Tech, M.Tech and MCA.",
    "exam": "End semester exams are conducted in March.",
    "library": "Library is open from 9 AM to 5 PM.",
    "placement": "Our college has 90% placement record."
}

chat_history = []

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    global chat_history

    if request.method == "POST":
        user_input = request.form["message"].lower()
        bot_reply = "Sorry, I don't understand."

        for key in responses:
            if key in user_input:
                bot_reply = responses[key]
                break

        chat_history.append(("You", user_input))
        chat_history.append(("Bot", bot_reply))

    return render_template("chat.html", chat_history=chat_history)

if __name__ == "__main__":
    app.run(debug=True)