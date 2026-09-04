// CareerCompass Core Interactive Logic

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initFlashAutoDismiss();
  initRoadmapCheckboxes();
  initDropzone();
  initSearchFilters();
});

// 1. Theme Switcher (Dark / Light Mode)
function initThemeToggle() {
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const currentTheme = localStorage.getItem('careercompass_theme') || 'dark';
  
  document.documentElement.setAttribute('data-theme', currentTheme);
  updateThemeIcon(currentTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const activeTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('careercompass_theme', newTheme);
      updateThemeIcon(newTheme);
    });
  }
}

function updateThemeIcon(theme) {
  const icon = document.getElementById('themeIcon');
  if (icon) {
    if (theme === 'light') {
      icon.className = 'fa-solid fa-moon text-primary';
    } else {
      icon.className = 'fa-solid fa-sun text-warning';
    }
  }
}

// 2. Flash Alert Auto-Dismiss
function initFlashAutoDismiss() {
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.classList.add('fade');
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });
}

// 3. Interactive Roadmap Checkboxes & Live API Sync
function initRoadmapCheckboxes() {
  const checkboxes = document.querySelectorAll('.milestone-checkbox');
  
  checkboxes.forEach(cb => {
    cb.addEventListener('change', async (e) => {
      const itemContainer = cb.closest('.milestone-item');
      const careerId = cb.dataset.careerId;
      const milestoneText = cb.dataset.milestone;
      const isChecked = cb.checked;
      const totalMilestones = document.querySelectorAll('.milestone-checkbox').length;

      if (isChecked) {
        itemContainer.classList.add('completed');
        triggerConfetti(e.clientX, e.clientY);
      } else {
        itemContainer.classList.remove('completed');
      }

      // Update backend via Fetch API
      try {
        const response = await fetch('/student/roadmap/toggle-milestone', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            career_id: careerId,
            milestone: milestoneText,
            completed: isChecked,
            total_milestones: totalMilestones
          })
        });

        const data = await response.json();
        if (data.success) {
          // Update progress UI elements
          const progressBar = document.getElementById('roadmapProgressBar');
          const progressText = document.getElementById('roadmapProgressPct');
          const completedCountEl = document.getElementById('completedMilestonesCount');

          if (progressBar) {
            progressBar.style.width = `${data.progress_percentage}%`;
            progressBar.setAttribute('aria-valuenow', data.progress_percentage);
          }
          if (progressText) {
            progressText.innerText = `${data.progress_percentage}%`;
          }
          if (completedCountEl) {
            completedCountEl.innerText = data.completed_count;
          }

          if (data.progress_percentage >= 100) {
            triggerMegaConfetti();
          }
        }
      } catch (err) {
        console.error('Failed to sync milestone:', err);
      }
    });
  });
}

// 4. Confetti Celebrations
function triggerConfetti(x, y) {
  if (typeof confetti === 'function') {
    confetti({
      particleCount: 40,
      spread: 60,
      origin: {
        x: x ? x / window.innerWidth : 0.5,
        y: y ? y / window.innerHeight : 0.5
      },
      colors: ['#2563eb', '#0284c7', '#06b6d4', '#38bdf8', '#10b981']
    });
  }
}

function triggerMegaConfetti() {
  if (typeof confetti === 'function') {
    const duration = 2.5 * 1000;
    const end = Date.now() + duration;

    (function frame() {
      confetti({
        particleCount: 4,
        angle: 60,
        spread: 55,
        origin: { x: 0 }
      });
      confetti({
        particleCount: 4,
        angle: 120,
        spread: 55,
        origin: { x: 1 }
      });

      if (Date.now() < end) {
        requestAnimationFrame(frame);
      }
    }());
  }
}

// 5. Resume File Upload Dropzone
function initDropzone() {
  const dropzone = document.getElementById('resumeDropzone');
  const fileInput = document.getElementById('resumeFileInput');
  const fileNameDisplay = document.getElementById('selectedFileName');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        updateFileName(fileInput.files[0].name);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) {
        updateFileName(fileInput.files[0].name);
      }
    });
  }

  function updateFileName(name) {
    if (fileNameDisplay) {
      fileNameDisplay.innerHTML = `<i class="fa-solid fa-file-pdf text-danger me-2"></i> Selected: <strong>${name}</strong>`;
      fileNameDisplay.classList.remove('d-none');
    }
  }
}

// 6. Dynamic Live Search Filters
function initSearchFilters() {
  const searchInput = document.getElementById('tableSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase().trim();
      const rows = document.querySelectorAll('.filterable-row');
      rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
      });
    });
  }
}
