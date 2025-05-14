// Fungsi untuk mengaktifkan/menonaktifkan menu navigasi pada tampilan mobile
function toggleMenu(event) {
    const navMenu = document.querySelector('.navbar .nav-menu');
    const userDropdown = document.querySelector('.navbar .user-dropdown');
    navMenu.classList.toggle('show');
    if (userDropdown && userDropdown.classList.contains('show')) {
        userDropdown.classList.remove('show');
    }
    event.stopPropagation();
}

// Fungsi untuk mengaktifkan/menonaktifkan dropdown menu pengguna
function toggleUserMenu(event) {
    const userDropdown = document.querySelector('.navbar .user-dropdown');
    const navMenu = document.querySelector('.navbar .nav-menu');
    if (userDropdown) {
        userDropdown.classList.toggle('show');
    }
    if (navMenu.classList.contains('show')) {
        navMenu.classList.remove('show');
    }
    event.stopPropagation();
}

// Fungsi untuk menutup menu saat klik di luar area menu
function closeMenusOnOutsideClick(event) {
    const navMenu = document.querySelector('.navbar .nav-menu');
    const userDropdown = document.querySelector('.navbar .user-dropdown');
    const hamburger = document.querySelector('.navbar .hamburger');
    const userBtn = document.querySelector('.navbar .user-btn');

    // Variabel dideklarasikan dengan garis bawah (underscore)
    const isClick_insideNavMenu = navMenu && navMenu.contains(event.target);
    const isClickOnHamburger = hamburger && hamburger.contains(event.target);
    const isClickInsideUserDropdown = userDropdown && userDropdown.contains(event.target);
    const isClickOnUserBtn = userBtn && userBtn.contains(event.target);
    // Memastikan bahwa variabel tidak null sebelum mengakses classList
    if (navMenu && !isClick_insideNavMenu && !isClickOnHamburger && navMenu.classList.contains('show')) {
        navMenu.classList.remove('show');
    }
    if (userDropdown && !isClickInsideUserDropdown && !isClickOnUserBtn && userDropdown.classList.contains('show')) {
        userDropdown.classList.remove('show');
    }
}

// Fungsi untuk menutup menu navigasi saat link diklik
function closeNavMenuOnLinkClick() {
    document.querySelectorAll('.navbar .nav-menu .nav-link').forEach(link => {
        link.addEventListener('click', function (e) {
            const navMenu = document.querySelector('.navbar .nav-menu');
            if (!(e.target.tagName === 'BUTTON' && e.target.closest('form'))) {
                if (navMenu && navMenu.classList.contains('show')) {
                    navMenu.classList.remove('show');
                }
            }
        });
    });
}

// Fungsi untuk menutup dropdown pengguna saat aksi pengguna diklik
function closeUserDropdownOnActionClick() {
    const userActions = document.querySelectorAll('.navbar .user-dropdown .user-action');
    if (userActions) {
        userActions.forEach(action => {
            action.addEventListener('click', function () {
                const userDropdown = document.querySelector('.navbar .user-dropdown');
                if (userDropdown) {
                    userDropdown.classList.remove('show');
                }
            });
        });
    }
}

// Inisiasi event listener
document.addEventListener('click', closeMenusOnOutsideClick);
closeNavMenuOnLinkClick();
closeUserDropdownOnActionClick();