/**
 * Splits element text into individual character spans.
 * Returns array of span elements for GSAP targeting.
 * Spaces become non-breaking spaces to preserve layout.
 */
export function splitChars(element) {
  const text = element.textContent;
  element.textContent = '';
  const spans = [];
  for (const char of text) {
    const span = document.createElement('span');
    span.className = 'char';
    span.textContent = char === ' ' ? '\u00A0' : char;
    span.style.display = 'inline-block';
    element.appendChild(span);
    spans.push(span);
  }
  return spans;
}

/**
 * Splits element text into word spans wrapped in overflow:hidden containers.
 * Returns array of inner word spans for GSAP targeting.
 */
export function splitWords(element) {
  const text = element.textContent;
  element.textContent = '';
  const words = text.split(' ');
  const innerSpans = [];
  words.forEach((word, i) => {
    const outer = document.createElement('span');
    outer.style.display = 'inline-block';
    outer.style.overflow = 'hidden';
    outer.style.verticalAlign = 'bottom';

    const inner = document.createElement('span');
    inner.className = 'word';
    inner.textContent = word;
    inner.style.display = 'inline-block';

    outer.appendChild(inner);
    element.appendChild(outer);

    if (i < words.length - 1) {
      element.appendChild(document.createTextNode(' '));
    }
    innerSpans.push(inner);
  });
  return innerSpans;
}
