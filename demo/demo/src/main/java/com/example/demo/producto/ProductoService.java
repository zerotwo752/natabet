package com.example.demo.producto;

import com.example.demo.tipoProducto.TipoProducto;

import java.util.List;

public interface ProductoService  {
    
    public List<Producto> ProductoReporte(Integer idTipoProducto);

    public void crearProductos(Producto Producto);
}
