package com.ucygym;

import jakarta.mail.Message;
import jakarta.mail.MessagingException;
import jakarta.mail.Session;
import jakarta.mail.Transport;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeMessage;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Properties;
import java.util.logging.Logger;

/** Telegram + Gmail alerts. */
public final class Notifier {
    private static final Logger log = Logger.getLogger(Notifier.class.getName());
    private static final HttpClient HTTP = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();

    private final String emailUser = Config.get("EMAIL_USER");
    private final String emailPass = Config.get("EMAIL_PASSWORD");
    private final String tgToken = Config.get("TELEGRAM_BOT_TOKEN");
    private final String tgChatId = Config.get("TELEGRAM_CHAT_ID");
    private final boolean tgEnabled = "true".equalsIgnoreCase(Config.get("TELEGRAM_ENABLED", "False"));

    public boolean sendTelegram(String message) {
        if (!tgEnabled || tgToken == null || tgChatId == null) return false;

        String form = "chat_id=" + encode(tgChatId) + "&text=" + encode(message);
        HttpRequest request = HttpRequest.newBuilder(URI.create("https://api.telegram.org/bot" + tgToken + "/sendMessage"))
                .timeout(Duration.ofSeconds(5))
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(form))
                .build();
        try {
            HttpResponse<String> response = HTTP.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() == 200) return true;
            log.warning("⚠️ Telegram send failed: HTTP " + response.statusCode() + " " + response.body());
        } catch (IOException e) {
            log.warning("⚠️ Telegram send failed: " + e.getMessage());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return false;
    }

    public boolean sendEmail(String recipient, String subject, String body) {
        if (emailUser == null || emailPass == null) {
            log.warning("⚠️ Email credentials missing.");
            return false;
        }
        if (recipient == null) {
            log.warning("⚠️ No recipient set (USER_EMAIL).");
            return false;
        }

        Properties props = new Properties();
        props.put("mail.smtp.host", "smtp.gmail.com");
        props.put("mail.smtp.port", "587");
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.starttls.enable", "true");
        props.put("mail.smtp.starttls.required", "true");
        props.put("mail.smtp.connectiontimeout", "10000");
        props.put("mail.smtp.timeout", "10000");
        try {
            MimeMessage msg = new MimeMessage(Session.getInstance(props));
            msg.setFrom(new InternetAddress(emailUser));
            msg.setRecipients(Message.RecipientType.TO, InternetAddress.parse(recipient));
            msg.setSubject(subject, "UTF-8");
            msg.setText(body, "UTF-8");
            Transport.send(msg, emailUser, emailPass);
            return true;
        } catch (MessagingException e) {
            log.warning("⚠️ Email send failed: " + e.getMessage());
            return false;
        }
    }

    /** Telegram always (if enabled); email only on failure, to avoid spam. */
    public void alert(boolean success, String recipient, String details) {
        String icon = success ? "✅" : "❌";
        String status = success ? "Success" : "Failed";
        sendTelegram(icon + " Gym Reservation " + status + "\n\n" + details);
        if (!success) sendEmail(recipient, icon + " Reservation " + status, details);
    }

    private static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }
}
