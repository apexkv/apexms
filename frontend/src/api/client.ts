import axios from "axios";

const apiClient = axios.create({
    baseURL: "http://localhost:14186/api/",
});

export default apiClient;