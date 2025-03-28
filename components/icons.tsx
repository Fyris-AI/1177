export const VercelIcon = ({ size = 17 }) => {
  return (
    <svg
      height={size}
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width={size}
      style={{ color: "currentcolor" }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M8 1L16 15H0L8 1Z"
        fill="currentColor"
      ></path>
    </svg>
  );
};

export const SearchIcon = ({ size = 25 }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 18 18"
      height={size}
      width={size}
    >
      <defs>
        <linearGradient id="a" x1="9" y1=".36" x2="9" y2="18.31" gradientUnits="userSpaceOnUse">
          <stop offset=".18" stopColor="#5ea0ef" />
          <stop offset="1" stopColor="#0078d4" />
        </linearGradient>
      </defs>
      <path
        d="M18 11.32a4.12 4.12 0 00-3.51-4 5.15 5.15 0 00-5.25-5 5.25 5.25 0 00-5 3.49A4.86 4.86 0 000 10.59a5 5 0 005.07 4.82h8.65a.78.78 0 00.22 0A4.13 4.13 0 0018 11.32z"
        fill="url(#a)"
      />
      <path
        d="M12.33 6.59a3.07 3.07 0 00-5.61.85 3.16 3.16 0 00.33 2.27l-2.34 2.37a.79.79 0 000 1.12.78.78 0 00.56.23.76.76 0 00.56-.23l2.33-2.36a3.14 3.14 0 00.81.33 3.08 3.08 0 003.36-4.58zm-.54 2.1a2.16 2.16 0 01-2.09 1.65 1.79 1.79 0 01-.51-.07 1.87 1.87 0 01-.7-.32 2.13 2.13 0 01-.56-.56 2.17 2.17 0 01-.31-1.73A2.14 2.14 0 019.7 6a2.31 2.31 0 01.52.06 2.18 2.18 0 011.32 1 2.13 2.13 0 01.25 1.63z"
        fill="#f2f2f2"
      />
      <ellipse cx="9.69" cy="8.18" rx="2.15" ry="2.16" fill="#83b9f9" />
    </svg>
  );
};

export const AzureIcon = ({ size = 25 }) => {
  return (
    <svg width={size} height={size} viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="e399c19f-b68f-429d-b176-18c2117ff73c" x1="-1032.172" x2="-1059.213" y1="145.312" y2="65.426" gradientTransform="matrix(1 0 0 -1 1075 158)" gradientUnits="userSpaceOnUse">
                <stop offset="0" stopColor="#114a8b"/>
                <stop offset="1" stopColor="#0669bc"/>
            </linearGradient>
            <linearGradient id="ac2a6fc2-ca48-4327-9a3c-d4dcc3256e15" x1="-1023.725" x2="-1029.98" y1="108.083" y2="105.968" gradientTransform="matrix(1 0 0 -1 1075 158)" gradientUnits="userSpaceOnUse">
                <stop offset="0" stopOpacity=".3"/>
                <stop offset=".071" stopOpacity=".2"/>
                <stop offset=".321" stopOpacity=".1"/>
                <stop offset=".623" stopOpacity=".05"/>
                <stop offset="1" stopOpacity="0"/>
            </linearGradient>
            <linearGradient id="a7fee970-a784-4bb1-af8d-63d18e5f7db9" x1="-1027.165" x2="-997.482" y1="147.642" y2="68.561" gradientTransform="matrix(1 0 0 -1 1075 158)" gradientUnits="userSpaceOnUse">
                <stop offset="0" stopColor="#3ccbf4"/>
                <stop offset="1" stopColor="#2892df"/>
            </linearGradient>
        </defs>
        <path fill="url(#e399c19f-b68f-429d-b176-18c2117ff73c)" d="M33.338 6.544h26.038l-27.03 80.087a4.152 4.152 0 0 1-3.933 2.824H8.149a4.145 4.145 0 0 1-3.928-5.47L29.404 9.368a4.152 4.152 0 0 1 3.934-2.825z"/>
        <path fill="#0078d4" d="M71.175 60.261h-41.29a1.911 1.911 0 0 0-1.305 3.309l26.532 24.764a4.171 4.171 0 0 0 2.846 1.121h23.38z"/>
        <path fill="url(#ac2a6fc2-ca48-4327-9a3c-d4dcc3256e15)" d="M33.338 6.544a4.118 4.118 0 0 0-3.943 2.879L4.252 83.917a4.14 4.14 0 0 0 3.908 5.538h20.787a4.443 4.443 0 0 0 3.41-2.9l5.014-14.777 17.91 16.705a4.237 4.237 0 0 0 2.666.972H81.24L71.024 60.261l-29.781.007L59.47 6.544z"/>
        <path fill="url(#a7fee970-a784-4bb1-af8d-63d18e5f7db9)" d="M66.595 9.364a4.145 4.145 0 0 0-3.928-2.82H33.648a4.146 4.146 0 0 1 3.928 2.82l25.184 74.62a4.146 4.146 0 0 1-3.928 5.472h29.02a4.146 4.146 0 0 0 3.927-5.472z"/>
    </svg>
  );
};
