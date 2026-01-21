/**
 * Authentication Page JavaScript
 * FINAL FIXED VERSION
 * Handles student login & registration
 */

document.addEventListener("DOMContentLoaded", function () {

    /* ===============================
       HARD RESET (SAFE FIX)
       Only reset on LOGIN page
    =============================== */
    if (window.location.pathname === "/") {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
    }

    /* ===============================
       HELPERS
    =============================== */
    function isLoggedIn() {
        return !!localStorage.getItem("token");
    }

    function getUser() {
        const user = localStorage.getItem("user");
        if (!user || user === "undefined" || user === "null") return null;
        try {
            return JSON.parse(user);
        } catch (err) {
            console.error("Invalid user JSON:", user);
            localStorage.removeItem("user");
            return null;
        }
    }

    /* ===============================
       AUTO REDIRECT IF LOGGED IN
    =============================== */
    if (isLoggedIn()) {
        const safeUser = getUser();
        if (!safeUser) {
            localStorage.clear();
            return;
        }

        if (safeUser.role === "admin") {
            window.location.replace("/admin");
        } else {
            window.location.replace("/dashboard");
        }
        return;
    }

    /* ===============================
       ELEMENTS
    =============================== */
    const loginStep = document.getElementById("loginStep");
    const registerStep = document.getElementById("registerStep");
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const showRegister = document.getElementById("showRegister");
    const showLogin = document.getElementById("showLogin");
    const alertContainer = document.getElementById("alertContainer");

    /* ===============================
       ALERT HANDLER
    =============================== */
    function showAlert(message, type = "error") {
        alertContainer.innerHTML = `
            <div class="alert alert-${type}">
                ${message}
            </div>
        `;
    }

    function clearAlert() {
        alertContainer.innerHTML = "";
    }

    /* ===============================
       TOGGLE LOGIN / REGISTER
    =============================== */
    showRegister?.addEventListener("click", (e) => {
        e.preventDefault();
        clearAlert();
        loginStep.classList.add("hidden");
        registerStep.classList.remove("hidden");
    });

    showLogin?.addEventListener("click", (e) => {
        e.preventDefault();
        clearAlert();
        registerStep.classList.add("hidden");
        loginStep.classList.remove("hidden");
    });

    /* ===============================
       LOGIN
    =============================== */
    loginForm?.addEventListener("submit", async function (e) {
        e.preventDefault();
        clearAlert();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        if (!email || !password) {
            showAlert("Email and password are required");
            return;
        }

        const submitBtn = loginForm.querySelector("button[type='submit']");
        submitBtn.disabled = true;
        submitBtn.textContent = "Logging in...";

        try {
            const response = await fetch("/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();

            if (response.ok && result.success) {

                localStorage.clear();
                localStorage.setItem("token", result.token);
                localStorage.setItem("user", JSON.stringify(result.user));

                window.location.replace(
                    result.user.role === "admin" ? "/admin" : "/dashboard"
                );
            } else {
                showAlert(result.message || "Invalid email or password");
            }
        } catch (error) {
            showAlert("Server connection error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "LOGIN";
        }
    });

    /* ===============================
       REGISTER
    =============================== */
    registerForm?.addEventListener("submit", async function (e) {
        e.preventDefault();
        clearAlert();

        const payload = {
            username: document.getElementById("fullName").value.trim(),
            email: document.getElementById("regEmail").value.trim(),
            password: document.getElementById("regPassword").value,
            mobile_number: document.getElementById("phone").value.trim(),
            dcet_reg_number: document.getElementById("regNo").value.trim(),
            college_name: document.getElementById("college").value.trim()
        };

        if (Object.values(payload).some(v => !v)) {
            showAlert("All fields are required");
            return;
        }

        const submitBtn = registerForm.querySelector("button[type='submit']");
        submitBtn.disabled = true;
        submitBtn.textContent = "Registering...";

        try {
            const response = await fetch("/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (response.ok && result.success) {

                showAlert(
                    "Registration successful ✅ Please check your email to confirm it is valid.",
                    "success"
                );

                registerForm.reset();

                // stay on same page
            } else {
                showAlert(result.message || "Registration failed");
            }
        } catch (error) {
            showAlert("Server connection error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "REGISTER";
        }
    });
});
