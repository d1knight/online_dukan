# Online Dúkan API

Bul proekt **Python** hám **Django REST Framework** tiykarında jaratılǵan tolıq funksional internet-dúkan API sisteması.

---

## 🚀 Múmkinshilikler

*   **Avtorizaciya:** Registraciya, Login (JWT Token), Admin hám Klient rolları.
*   **Tawarlar:** Izlew (Search), Baha boyınsha filtr (min/max), Kategoriyalar.
*   **Sebet (Cart):** Qosıw, óshiriw hám esaplaw.
*   **Buyırtpa (Order):** "Checkout" waqtında skladdan tawarlardı avtomat túrde ayırıw.
*   **Qosımsha:** Docker, Swagger hújjetlesiwi, Pikirler (Reviews).

---

## 🛠 Texnologiyalar

- **Til:** Python 3.10+
- **Framework:** Django 4.x, DRF
- **Baza:** PostgreSQL
- **Tools:** Docker, Swagger (drf-yasg)

---

## ⚙️ Iske túsiriw (Docker arqalı)

Eń ańsat jolı — Docker-den paydalanıw.

1.  **Repozitoriydi júklep alıń:**
    ```bash
    git clone https://github.com/d1knight/online_dukan.git
    cd online_store
    ```

2.  **`.env` fayl jaratıń:**
    Proekt papkasında `.env` fayl jaratıp, tómendegilerdi jazıń:
    ```ini
    DEBUG=True
    SECRET_KEY=jasirin-kod-123
    ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

    DB_NAME=dukan_db
    DB_USER=postgres
    DB_PASSWORD=Nesli2024
    DB_HOST=db
    DB_PORT=5432
    ```

3.  **Proektti iske túsiriń:**
    ```bash
    docker-compose up --build
    ```

4.  **Admin (Superuser) jaratıw:**
    Jańa terminal ashıp, tómendegi komandanı jazıń:
    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```

---

## 📖 API Dokumentaciyasi (Swagger)

Proekt iske túskennen soń, barlıq API endpointlerdi tómendegi silteme arqalı kóriw múmkin:

👉 **[http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)**


## 👤 Avtor: Maman Dauletov

Repozitoriy: [github.com/d1knight/online-dukan](https://github.com/d1knight/online_dukan)