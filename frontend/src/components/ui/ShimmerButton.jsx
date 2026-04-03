export function ShimmerButton({ children, onClick, style = {}, className = "", ...props }) {
  return (
    <button
      onClick={onClick}
      className={`shimmer-btn ${className}`}
      style={style}
      {...props}
    >
      {children}
    </button>
  );
}
