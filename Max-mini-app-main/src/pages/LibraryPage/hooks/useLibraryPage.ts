import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { App } from "antd";
import { useLibraryAccessQuery } from "@/hooks/queries";
import { transformLibraryAccessForPage, type LibraryAccessViewModel } from "../lib/transformLibraryAccess";

/**
 * Хук для управления логикой страницы библиотеки
 */
export function useLibraryPage() {
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);

  const { data: apiData, isLoading, error } = useLibraryAccessQuery();
  const libraryData: LibraryAccessViewModel | null = apiData ? transformLibraryAccessForPage(apiData) : null;

  const handleCopy = useCallback(
    async (text: string) => {
      try {
        await navigator.clipboard.writeText(text);
        message.success("Успешно скопировано");
      } catch (error) {
        message.error("Ошибка при копировании");
      }
    },
    [message]
  );

  const togglePasswordVisibility = useCallback(() => {
    setIsPasswordVisible((prev) => !prev);
  }, []);

  const handleBack = useCallback(() => {
    navigate(-1);
  }, [navigate]);

  return {
    libraryData,
    isLoading,
    error,
    isPasswordVisible,
    handleCopy,
    togglePasswordVisibility,
    handleBack,
  };
}
