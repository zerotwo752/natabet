<%@ taglib uri="http://www.springframework.org/tags/form" prefix="form" %>
<%@ page contentType="text/html; charset=UTF-8" %>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Crear Tipo de Producto</title>
</head>
<body>
<h1>Crear Tipo de Producto</h1>
<!-- El formulario está vinculado al objeto "tipoProducto" -->
<form:form action="/producto/crear" method="post" modelAttribute="Producto">
    <label for="nombre">Nombre:</label>
    <form:input path="nombre" id="nombre" required="true"/>
    <br>
    <label for="fechaCreacion">Fecha de Creación:</label>
    <form:input path="fechaCreacion" id="fecha_creacion" type="date" required="true" />
    <br>
    <label for="tipoProducto">Tipo de Producto:</label>
    <form:select path="tipoProducto.id" id="tipoProducto">
        <form:options items="${tipoproductos}" var="tipoProducto" itemValue="id" itemLabel="nombre"/>
    </form:select>
    <button type="submit">Crear</button>
</form:form>
<a href="/producto/list">Volver a la lista</a>
</body>
</html>