import React from "react";

export const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <main>
      <div className="flex flex-col flex-wrap w-full max-w-screen-xl px-4 mx-auto">
        <div className="mt-4 mb-4">
          <p className="text-3xl font-bold">clipsynce</p>
        </div>
        {children}
      </div>
    </main>
  );
};
