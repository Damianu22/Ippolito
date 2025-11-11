document.addEventListener('DOMContentLoaded', () => {
	const flashMessages = document.querySelectorAll('.flash');
	flashMessages.forEach((flash) => {
		flash.addEventListener('click', () => flash.remove());
		setTimeout(() => {
			flash.classList.add('is-fading');
			setTimeout(() => flash.remove(), 600);
		}, 6000);
	});
});
