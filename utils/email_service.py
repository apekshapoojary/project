from flask_mail import Mail, Message
from flask import current_app

mail = Mail()

def send_registration_email(to_email, user_name, event_name, event_date, registration_time):
    try:
        msg = Message(f"Registration Confirmed: {event_name}",
                      recipients=[to_email])
        msg.body = (f"Hi {user_name},\n\n"
                    f"You have successfully registered for {event_name}.\n\n"
                    f"Registration Details:\n"
                    f"- Event Date: {event_date}\n"
                    f"- Confirmed At: {registration_time}\n\n"
                    f"Please show your institutional dashboard at the venue to scan the event attendance QR code on the day of the event.\n\n"
                    f"Best regards,\nCampus Prestige Team")
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_certificate_email(to_email, user_name, event_name, pdf_path):
    try:
        msg = Message(f"Your Certificate of Achievement: {event_name}",
                      recipients=[to_email])
        msg.body = f"Hi {user_name},\n\nCongratulations! You have completed {event_name}. Please find your certificate attached.\n\nBest regards,\nEventLink Team"
        
        with current_app.open_resource(pdf_path) as fp:
            msg.attach(f"Certificate_{event_name.replace(' ', '_')}.pdf", "application/pdf", fp.read())
            
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send certificate email: {e}")
        return False
