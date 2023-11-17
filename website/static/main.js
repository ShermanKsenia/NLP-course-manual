const searchIcon = document.querySelector(
    ".search-icon-container .search-icon"
);   
const searchInput = document.querySelector(
    ".search-input-container input"
);
const closeIcon = document.querySelector(
    ".search-icon-container .close-icon"
);
const mobileCloseIcon = document.querySelector(
    ".mobile-menu-container .close-icon"
);
const mobileMenuContainer = document.querySelector(".mobile-menu-container");
const menuIcon = document.querySelector("nav .menu-icon");

searchIcon.addEventListener("click", () => {
    searchInput.classList.add("active");
    closeIcon.classList.add("active");
    searchIcon.classList.remove("active");
});

closeIcon.addEventListener("click", () => {
    searchInput.classList.remove("active");
    closeIcon.classList.remove("active");
    searchIcon.classList.add("active");
});

menuIcon.addEventListener("click", () => {
    mobileMenuContainer.classList.add("active");
});

mobileCloseIcon.addEventListener("click", () => {
    mobileMenuContainer.classList.remove("active");
});
