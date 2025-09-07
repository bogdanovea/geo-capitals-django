document.addEventListener('DOMContentLoaded', () => {
    const wrap = document.querySelector('.messages');
    if (!wrap) return;

    const msgs = wrap.querySelectorAll('.msg');
    msgs.forEach((el, i) => {
      // 3s до скрытия, со сдвигом в 250ms между сообщениями (чтоб не схлопнулись разом)
      const delay = 3000 + i * 250;
      setTimeout(() => {
        el.classList.add('fade-out');
        // удаляем DOM-узел после анимации
        setTimeout(() => {
          el.remove();
          // если сообщений не осталось — убираем контейнер
          if (!wrap.querySelector('.msg')) wrap.remove();
        }, 350);
      }, delay);
    });
  });