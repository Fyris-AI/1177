"use client";
import React, { createContext, useContext, useState } from "react";

interface ConfigContextType {
  config: {
    openLinksInNewTab: boolean;
  };
  setConfig: (config: { openLinksInNewTab: boolean }) => void;
}

const ConfigContext = createContext<ConfigContextType>({
  config: {
    openLinksInNewTab: false,
  },
  setConfig: () => {},
});

export const ConfigProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [config, setConfig] = useState({
    openLinksInNewTab: false,
  });

  return (
    <ConfigContext.Provider value={{ config, setConfig }}>
      {children}
    </ConfigContext.Provider>
  );
};

export const useConfig = () => useContext(ConfigContext);
