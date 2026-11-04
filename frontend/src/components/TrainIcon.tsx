interface TrainIconProps {
  className?: string;
}

// Outline of a train carriage, nose to the right. Decorative only.
function TrainIcon({ className }: TrainIconProps) {
  return (
    <svg
      className={className}
      width="34"
      height="22"
      viewBox="0 0 34 22"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M2 3h20c5.5 0 9 4 9 9v3H2z" />
      <path d="M6 6.5h4v4H6zM13 6.5h4v4h-4z" />
      <path d="M21 6.5h2.5c2 0 3.6 1.6 4 4H21z" />
      <circle cx="8" cy="17.5" r="1.6" />
      <circle cx="24" cy="17.5" r="1.6" />
      <path d="M1 21h32" />
    </svg>
  );
}

export default TrainIcon;
