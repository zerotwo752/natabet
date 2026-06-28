package com.example.demo.producto;

import com.example.demo.tipoProducto.TipoProducto;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import com.example.demo.tipoProducto.TipoProductoService;
import com.example.demo.producto.ProductoService;

@Controller
@RequestMapping("/producto")
public class ProductoController {

    private final TipoProductoService tipoProductoService;
    private final ProductoService productoService;


    public ProductoController(TipoProductoService tipoProductoService, ProductoService productoService) {
        this.tipoProductoService = tipoProductoService;
        this.productoService = productoService;
    }

    @RequestMapping("/list")
    public String listaTipoProducto(Model model) {
        model.addAttribute("tipoproductos", tipoProductoService.listaTipoProducto());      
        return "producto/reporte/producto_list"; // Retorna la vista correspondiente
    }

    @GetMapping("/crear")
    public String mostrarFormularioCrear(Model model) {
        model.addAttribute("Producto", new Producto());
        model.addAttribute("tipoproductos", tipoProductoService.listaTipoProducto());
        return "producto/crearproducto";
    }

    @PostMapping("/crear")
    public String crearProducto(@ModelAttribute("Producto") Producto Producto) {
        productoService.crearProductos(Producto);
        return "redirect:/producto/crear";
    }

    @PostMapping("/reporte/productoTipoProducto")
    public String ReporteProducto( @RequestParam("id") int id , Model model) {
        model.addAttribute("productos", productoService.ProductoReporte(id));   
        return "producto/reporte/producto"; // Retorna la vista correspondiente
    }


}
