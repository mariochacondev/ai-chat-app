import React from "react";
import ReactDOM from "react-dom/client";
import {createBrowserRouter, Navigate, RouterProvider} from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import Auth from "./pages/Auth"
import DocsPage from "./pages/DocsPage";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminUsersPage from "./pages/AdminUserPage.tsx";
import AdminRoute from "./components/AdminRoute";

const router = createBrowserRouter([
    {
        path: "/",
        element: <Navigate to="/auth" replace/>,
    },
    {
        path: "/auth",
        element: <Auth/>,
    },
    {
        path: "/docs",
        element: (
            <ProtectedRoute>
                <DocsPage/>
            </ProtectedRoute>
        ),
    },
    {
        path: "/chat",
        element: (
            <ProtectedRoute>
                <ChatPage/>
            </ProtectedRoute>
        ),
    },
    {
        path: "/admin/users",
        element: (
            <ProtectedRoute>
                <AdminRoute>
                    <AdminUsersPage/>
                </AdminRoute>
            </ProtectedRoute>
        ),
    },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <RouterProvider router={router}/>
    </React.StrictMode>
);
