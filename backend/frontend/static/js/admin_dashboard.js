// frontend/static/js/admin_dashboard.js

document.addEventListener("DOMContentLoaded", () => {
  // 이 페이지가 아닌 곳에서는 그냥 종료
  const adminPage = document.querySelector(".admin-page");
  if (!adminPage) return;

  initAdminPage();
});

async function initAdminPage() {
  try {
    //개발용 임시: /api/auth/me/ 체크 잠깐 끔
    const meRes = await authFetch("/api/auth/me/");
    if (!meRes.ok) {
      alert("로그인이 필요합니다.");
      window.location.href = "/login/";
      return;
    }
    const me = await meRes.json();
    const role = me.role || me.user_role || me.member_role || null;
    if (role !== "ADMIN") {
      alert("관리자만 접근할 수 있습니다.");
      window.location.href = "/";
      return;
    }

    // 2) 통계, 신고, 신규회원 불러오기
    loadAdminStats();
    loadReportList();
    loadNewMembers();
  } catch (err) {
    console.error("admin init error:", err);
    alert("관리자 페이지를 불러오는 중 오류가 발생했습니다.");
    window.location.href = "/";
  }
}

/***********************
 *  통계 카드 로딩 (선택)
 ***********************/
async function loadAdminStats() {
  try {
    const res = await authFetch("/api/admin/dashboard/");
    if (!res.ok) return;
    const data = await res.json();

    const el = (id) => document.getElementById(id);

    if (el("statTotalUsers"))
      el("statTotalUsers").textContent = data.total_users ?? "-";
    if (el("statTotalRecipes"))
      el("statTotalRecipes").textContent = data.total_recipes ?? "-";
    if (el("statTotalLikes"))
      el("statTotalLikes").textContent = data.total_likes ?? "-";
    if (el("statDailyVisitors"))
      el("statDailyVisitors").textContent = data.daily_visitors ?? "-";
  } catch (err) {
    console.error("loadAdminStats error:", err);
  }
}

/***********************
 *  신고 내역 리스트
 ***********************/
async function loadReportList() {
  const listEl = document.getElementById("reportList");
  const errorEl = document.getElementById("reportError");
  if (!listEl) return;

  listEl.innerHTML = "";
  if (errorEl) errorEl.textContent = "";

  try {
    const res = await authFetch("/api/admin/reports/");
    if (!res.ok) {
      if (errorEl) errorEl.textContent = "신고 내역을 불러오지 못했습니다.";
      return;
    }

    const reports = await res.json();

    if (!Array.isArray(reports) || reports.length === 0) {
      listEl.innerHTML = "<p>신고된 내용이 없습니다.</p>";
      return;
    }

    reports.slice(0, 5).forEach((report) => {
      const item = document.createElement("div");
      item.className = "report-item";

      const reporterName =
        report.reporter?.name ||
        report.reporter?.login_id ||
        "알 수 없음";

      let targetText = "알 수 없음";
      if (report.target_type === "RECIPE") {
        targetText = `레시피 #${report.recipe_id}`;
      } else if (report.target_type === "COMMENT") {
        targetText = `댓글 #${report.comment_id}`;
      }

      const reason = report.reason || "(사유 없음)";
      const createdDate = (report.created_at || "").slice(0, 10);

      const isResolved = report.status === "RESOLVED";
      const statusText = isResolved ? "처리완료" : "대기";
      const statusClass = isResolved ? "resolved" : "processing";

      item.innerHTML = `
        <div class="report-title">${reason}</div>
        <div class="report-date">${createdDate}</div>
        <div class="report-status ${statusClass}">
          ${statusText}
        </div>
        <div class="report-subtext">
          대상: ${targetText} · 신고자: ${reporterName}
        </div>
        <div class="report-actions">
          ${
            isResolved
              ? `<button class="report-btn secondary" data-id="${report.report_id}" disabled>처리 완료</button>`
              : `<button class="report-btn primary" data-id="${report.report_id}">처리하기</button>`
          }
        </div>
      `;

      listEl.appendChild(item);
    });

    // 버튼 이벤트 연결
    listEl.querySelectorAll(".report-btn.primary").forEach((btn) => {
      btn.addEventListener("click", () => {
        const reportId = btn.getAttribute("data-id");
        handleReport(reportId);
      });
    });
  } catch (err) {
    console.error("loadReportList error:", err);
    if (errorEl) {
      errorEl.textContent = "신고 내역을 불러오는 중 오류가 발생했습니다.";
    }
  }
}

/***********************
 *  신고 처리
 ***********************/
async function handleReport(reportId) {
  if (!reportId) return;

  const confirmResult = confirm(`신고 #${reportId} 를 처리 상태로 변경하시겠습니까?`);
  if (!confirmResult) return;

  const note = prompt("처리 메모를 입력하세요. (선택 사항)", "") || "";

  try {
    const body = {
      status: "RESOLVED",
    };
    if (note.trim()) {
      body.handle_note = note.trim();
    }

    const res = await authFetch(`/api/admin/reports/${reportId}/`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      alert("신고 처리에 실패했습니다.");
      return;
    }

    alert("신고가 처리되었습니다.");
    loadReportList();
  } catch (err) {
    console.error("handleReport error:", err);
    alert("신고 처리 중 오류가 발생했습니다.");
  }
}

/***********************
 *  신규 회원 (있다면)
 ***********************/
async function loadNewMembers() {
  const listEl = document.getElementById("memberList");
  const errorEl = document.getElementById("memberError");
  if (!listEl) return;

  listEl.innerHTML = "";
  if (errorEl) errorEl.textContent = "";

  try {
    const res = await authFetch("/api/admin/members/recent/");
    if (!res.ok) {
      if (errorEl) errorEl.textContent = "신규 회원 목록을 불러오지 못했습니다.";
      return;
    }

    const members = await res.json();

    if (!Array.isArray(members) || members.length === 0) {
      listEl.innerHTML = "<p>신규 회원이 없습니다.</p>";
      return;
    }

    members.slice(0, 5).forEach((m) => {
      const item = document.createElement("div");
      item.className = "member-item";

      const name = m.name || m.username || "알 수 없음";
      const email = m.email || m.login_id || "-";
      const recipesCount = m.recipes_count ?? 0;
      const joined = (m.created_at || m.date_joined || "").slice(0, 10);

      item.innerHTML = `
        <div class="member-main">
          <span class="member-name">${name}</span>
          <span class="member-email">${email}</span>
        </div>
        <div class="member-meta">
          <div>${recipesCount} 레시피</div>
          <div>${joined}</div>
        </div>
      `;

      listEl.appendChild(item);
    });
  } catch (err) {
    console.error("loadNewMembers error:", err);
    if (errorEl) {
      errorEl.textContent = "신규 회원을 불러오는 중 오류가 발생했습니다.";
    }
  }
}
