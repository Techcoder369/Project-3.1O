/**
 * Dashboard Page JavaScript
 * Displays subject cards for DCET preparation
 * + Email verified badge
 * + Auto login after verification
 * + Resend verification email
 */

document.addEventListener("DOMContentLoaded", async () => {

  // =====================================================
  // AUTO LOGIN AFTER EMAIL VERIFICATION (TOKEN IN URL)
  // =====================================================
  const urlParams = new URLSearchParams(window.location.search);
  const tokenFromUrl = urlParams.get("token");

  if (tokenFromUrl) {
    localStorage.setItem("token", tokenFromUrl);
    // clean URL
    window.history.replaceState({}, document.title, "/dashboard");
  }

  // =====================================================
  // AUTH CHECK
  // =====================================================
  if (!requireAuth()) return;

  const user = getUser();

  // =====================================================
  // USER NAME
  // =====================================================
  const userNameEl = document.getElementById("userName");
  if (userNameEl) {
    userNameEl.textContent =
      user?.username || user?.dcet_reg_number || "Student";
  }

  // =====================================================
  // EMAIL VERIFIED BADGE
  // =====================================================
  renderEmailBadge(user);

  await loadSubjects();
});


/* =====================================================
   EMAIL VERIFIED BADGE + RESEND BUTTON
===================================================== */
function renderEmailBadge(user) {
  const header = document.querySelector(".dashboard-header");
  if (!header || !user) return;

  const badge = document.createElement("div");
  badge.className = "email-verify-badge";

  if (user.email_verified) {
    badge.innerHTML = `
      <span class="verified">✅ Email Verified</span>
    `;
  } else {
    badge.innerHTML = `
      <span class="not-verified">⚠ Email Not Verified</span>
      <button id="resendVerifyBtn" class="btn-link">Resend verification email</button>
    `;
  }

  header.appendChild(badge);

  const resendBtn = document.getElementById("resendVerifyBtn");
  if (resendBtn) {
    resendBtn.addEventListener("click", resendVerificationEmail);
  }
}


/* =====================================================
   RESEND VERIFICATION EMAIL
===================================================== */
async function resendVerificationEmail() {
  const user = getUser();
  if (!user?.email) return;

  try {
    const res = await fetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: user.username,
        email: user.email,
        password: "dummy",            // backend ignores because already exists
        dcet_reg_number: "dummy",
        college_name: "dummy"
      })
    });

    const result = await res.json();

    alert("📩 Verification email sent again. Please check your inbox.");
  } catch (err) {
    alert("❌ Failed to resend verification email");
  }
}


/* =====================================================
   SUBJECTS
===================================================== */
async function loadSubjects() {
  const subjectGrid = document.getElementById("subjectGrid");
  if (!subjectGrid) return;

  subjectGrid.innerHTML = `
    <article class="subject-card loading-card">
      <div class="spinner"></div>
      <p>Loading subjects...</p>
    </article>
  `;

  const result = await SubjectAPI.getAll();

  if (!result.success) {
    subjectGrid.innerHTML =
      '<div class="alert alert-error">Failed to load subjects. Please refresh the page.</div>';
    return;
  }

  const iconMap = {
    calculate: "📐",
    assignment: "📋",
    electrical_services: "⚡",
    analytics: "📊",
    computer: "💻",
  };

  subjectGrid.innerHTML = result.subjects
    .map((subject) => {
      const icon = iconMap[subject.icon] || "📚";
      const desc = subject.description || "Core concepts for DCET preparation";
      return `
        <article class="subject-card" data-subject-id="${subject.id}">
          <div class="subject-icon">${icon}</div>
          <h2 class="subject-title">${subject.name}</h2>
          <p class="subject-tagline">${desc}</p>
          <button class="btn-gradient" type="button">Start Practice →</button>
        </article>
      `;
    })
    .join("");

  document.querySelectorAll(".subject-card").forEach((card) => {
    const id = card.dataset.subjectId;
    if (!id) return;

    card.addEventListener("click", () => {
      const selected = result.subjects.find(
        (s) => String(s.id) === String(id)
      );
      if (selected) {
        localStorage.setItem("selectedSubject", JSON.stringify(selected));
      }
      window.location.href = `/pages/subject.html?id=${id}`;
    });
  });
}
